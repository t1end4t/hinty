from pathlib import Path

from hinty.tools.rag import tool_rag


def main():
    """Run a simple test of the RAG tool."""
    # Example usage - replace with actual PDF path and query
    query = "What is the main topic of this document?"
    pdf_path = Path("example.pdf")  # Replace with actual PDF path

    result = tool_rag(query=query, pdf_path=pdf_path)
    print("RAG Tool Result:")
    print(result)


if __name__ == "__main__":
    main()
