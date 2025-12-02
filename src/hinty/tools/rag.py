from pathlib import Path
from typing import Any, Dict, List, Optional

import nltk
import numpy as np
from loguru import logger
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)


def parse_pdf_with_marker(pdf_path: Path) -> str:
    """
    Parse PDF to Markdown using Marker library.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Markdown content as string
    """
    logger.info(f"Parsing PDF: {pdf_path}")

    try:
        # Load models once (cache them)
        models = load_all_models()

        # Convert PDF to markdown
        markdown_text, images, metadata = convert_single_pdf(
            str(pdf_path), models
        )

        logger.info(f"Successfully parsed PDF: {pdf_path}")
        return markdown_text

    except ImportError:
        logger.error(
            "Marker library not installed. Install with: pip install marker-pdf"
        )
        raise
    except Exception as e:
        logger.error(f"Failed to parse PDF {pdf_path}: {e}")
        raise


def chunk_text_hierarchical(
    text: str, chunk_size: int = 512, overlap: int = 128
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks with parent-child relationships.

    Args:
        text: Input text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks

    Returns:
        List of chunk dictionaries with metadata
    """
    logger.debug(f"Chunking text of length {len(text)}")

    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]

        # Create parent chunk (larger context)
        parent_start = max(0, start - overlap)
        parent_end = min(len(text), end + overlap)
        parent_text = text[parent_start:parent_end]

        chunks.append(
            {
                "id": chunk_id,
                "text": chunk_text,
                "parent_text": parent_text,
                "start": start,
                "end": end,
            }
        )

        start += chunk_size - overlap
        chunk_id += 1

    logger.debug(f"Created {len(chunks)} chunks")
    return chunks


def create_hybrid_index(
    chunks: List[Dict[str, Any]], model_name: str = "BAAI/bge-small-en-v1.5"
) -> Dict[str, Any]:
    """
    Create hybrid index with dense and sparse vectors.

    Args:
        chunks: List of text chunks
        model_name: Name of the sentence transformer model

    Returns:
        Dictionary containing dense embeddings and BM25 index
    """
    logger.info("Creating hybrid index")

    # Dense vectors (semantic search)
    model = SentenceTransformer(model_name)
    texts = [chunk["text"] for chunk in chunks]
    dense_embeddings = model.encode(texts, show_progress_bar=True)

    # Sparse vectors (BM25 for keyword search)
    tokenized_texts = [word_tokenize(text.lower()) for text in texts]
    bm25 = BM25Okapi(tokenized_texts)

    logger.info("Hybrid index created successfully")

    return {
        "dense_model": model,
        "dense_embeddings": dense_embeddings,
        "bm25": bm25,
        "tokenized_texts": tokenized_texts,
        "chunks": chunks,
    }


def hybrid_search(
    query: str,
    index: Dict[str, Any],
    top_k: int = 10,
    alpha: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining dense and sparse retrieval.

    Args:
        query: Search query
        index: Hybrid index created by create_hybrid_index
        top_k: Number of results to return
        alpha: Weight for dense vs sparse (0=sparse only, 1=dense only)

    Returns:
        List of retrieved chunks with scores
    """
    logger.info(f"Performing hybrid search for query: {query[:50]}...")

    # Dense search
    query_embedding = index["dense_model"].encode([query])[0]
    dense_scores = np.dot(index["dense_embeddings"], query_embedding)

    # Normalize dense scores
    dense_scores = (dense_scores - dense_scores.min()) / (
        dense_scores.max() - dense_scores.min() + 1e-10
    )

    # Sparse search (BM25)
    tokenized_query = word_tokenize(query.lower())
    sparse_scores = index["bm25"].get_scores(tokenized_query)

    # Normalize sparse scores
    sparse_scores = (sparse_scores - sparse_scores.min()) / (
        sparse_scores.max() - sparse_scores.min() + 1e-10
    )

    # Combine scores
    hybrid_scores = alpha * dense_scores + (1 - alpha) * sparse_scores

    # Get top-k indices
    top_indices = np.argsort(hybrid_scores)[-top_k:][::-1]

    results = [
        {
            **index["chunks"][idx],
            "score": float(hybrid_scores[idx]),
            "dense_score": float(dense_scores[idx]),
            "sparse_score": float(sparse_scores[idx]),
        }
        for idx in top_indices
    ]

    logger.info(f"Retrieved {len(results)} results")
    return results


def rerank_results(
    query: str,
    results: List[Dict[str, Any]],
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Rerank results using a cross-encoder model.

    Args:
        query: Search query
        results: List of search results
        model_name: Name of the cross-encoder model
        top_k: Number of top results to return (None = all)

    Returns:
        Reranked list of results
    """
    logger.info("Reranking results with cross-encoder")

    reranker = CrossEncoder(model_name)

    # Prepare pairs for reranking
    pairs = [[query, result["text"]] for result in results]

    # Get reranking scores
    rerank_scores = reranker.predict(pairs)

    # Add rerank scores to results
    for result, score in zip(results, rerank_scores):
        result["rerank_score"] = float(score)

    # Sort by rerank score
    reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)

    if top_k:
        reranked = reranked[:top_k]

    logger.info(f"Reranking complete, returning {len(reranked)} results")
    return reranked


def rag_query(
    query: str,
    pdf_path: Path,
    top_k: int = 5,
    chunk_size: int = 512,
    overlap: int = 128,
    alpha: float = 0.5,
    use_reranker: bool = True,
) -> List[Dict[str, Any]]:
    """
    Complete RAG pipeline: parse PDF, index, search, and rerank.

    Args:
        query: Search query
        pdf_path: Path to PDF file
        top_k: Number of final results to return
        chunk_size: Size of text chunks
        overlap: Overlap between chunks
        alpha: Weight for dense vs sparse search
        use_reranker: Whether to use cross-encoder reranking

    Returns:
        List of relevant chunks with scores
    """
    logger.info(f"Starting RAG query for: {query[:50]}...")

    # Step 1: Parse PDF
    markdown_text = parse_pdf_with_marker(pdf_path)

    # Step 2: Chunk text
    chunks = chunk_text_hierarchical(markdown_text, chunk_size, overlap)

    # Step 3: Create hybrid index
    index = create_hybrid_index(chunks)

    # Step 4: Hybrid search
    initial_results = hybrid_search(
        query, index, top_k=top_k * 2 if use_reranker else top_k, alpha=alpha
    )

    # Step 5: Rerank (optional)
    if use_reranker:
        final_results = rerank_results(query, initial_results, top_k=top_k)
    else:
        final_results = initial_results[:top_k]

    logger.info(f"RAG query complete, returning {len(final_results)} results")
    return final_results
