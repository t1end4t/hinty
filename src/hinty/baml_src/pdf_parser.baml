class ContentBlock {
    id string
    type string // "text" | "table" | "image" | "list" | "heading"
    content string
    structured_data map<string, string>?
    semantic_tags string[]
    context string
    page_number int
    position int
}

class PageMetadata {
    page_number int
    has_continuation_from_previous bool // Does content continue from previous page?
    continues_to_next bool // Does content continue to next page?
    section_name string? // Current section/chapter name if identifiable
}

class PDFPageDocument {
    page_summary string
    content_blocks ContentBlock[]
    key_entities map<string, string[]>?
    metadata PageMetadata
}

function PdfParser(pdf_input: pdf, page_number: int, previous_page_context: string?) -> PDFPageDocument {
    client GeminiGeneral
    prompt #"
    You are parsing a PDF page-by-page. This is PAGE {{ page_number }}.

    {% if previous_page_context %}
    CONTEXT FROM PREVIOUS PAGE:
    {{ previous_page_context }}
    
    Important: Check if any content on this page is a continuation from the previous page.
    {% endif %}

    Your task: Extract and structure this single page into intelligent, queryable blocks.

    ## STEP 1: Analyze Page Context
    - What section/chapter is this page part of? (look for headers, footers, section titles)
    - Does content start mid-sentence or mid-paragraph? (continuation from previous page)
    - Does content end incomplete? (continues to next page)
    - What's the primary topic/purpose of THIS page?

    ## STEP 2: Extract Content Blocks
    Create a ContentBlock for each distinct piece of content:

    **ID Format**: "p{{ page_number }}_block_N" or "p{{ page_number }}_table_N" or "p{{ page_number }}_image_N"
    
    **Type Classification**:
    - "heading": Titles, section headers (include heading level in structured_data)
    - "text": Paragraphs, body content
    - "table": Tabular data
    - "list": Bullet points or numbered lists
    - "image": Charts, diagrams, photos

    **Content**: 
    - For text/lists: Full markdown content
    - For tables: Markdown table + structured JSON in structured_data
    - For images: Detailed description including what it shows and its purpose

    **Structured Data** (when applicable):
    - Tables: {{"{"}} "headers": [...], "rows": [[...]], "caption": "..." {{"}"}}
    - Headings: {{"{"}} "level": 1-6, "is_section_start": true/false {{"}"}}
    - Lists: {{"{"}} "list_type": "bullet"|"numbered", "items": [...] {{"}"}}

    **Semantic Tags** (critical for retrieval):
    Think: "What would someone search for to find this content?"
    Examples:
    - ["executive_summary", "key_findings"]
    - ["financial_results", "Q4_2024", "revenue"]
    - ["methodology", "technical", "data_collection"]
    - ["pricing", "product_features"]
    - ["conclusion", "recommendations"]
    - ["introduction", "background"]
    
    Be specific AND broad: ["sales_data", "financial", "2024"]

    **Context** (help future retrieval understand this block):
    Describe WHERE and WHY this appears. Examples:
    - "Opening paragraph of the 'Market Analysis' section"
    - "Summary table showing quarterly revenue breakdown"
    - "Chart illustrating customer growth trends, referenced in conclusion"
    - "Continuation of methodology discussion from previous page"

    **Position**: Number blocks sequentially as they appear (1, 2, 3...)

    ## STEP 3: Extract Key Entities (from this page only)
    Look for:
    - **people**: Names of individuals mentioned
    - **organizations**: Companies, institutions
    - **dates**: Specific dates or time periods
    - **locations**: Places, regions, countries
    - **metrics**: Important numbers with context (e.g., "$1.2M revenue", "45% growth")
    - **products**: Product or service names

    ## STEP 4: Page Metadata
    - **page_number**: {{ page_number }}
    - **has_continuation_from_previous**: Does this page continue content from previous page?
    - **continues_to_next**: Does content end incomplete (likely continues next page)?
    - **section_name**: What section/chapter is this page in?

    ## STEP 5: Page Summary
    Write 2-3 sentences summarizing ONLY this page's content. Focus on:
    - Main topics covered
    - Key information presented
    - How it fits in the document flow

    ---

    CRITICAL RULES:
    1. **Completeness**: Extract ALL visible content - don't skip anything
    2. **Accuracy**: Transcribe text exactly, preserve table data precisely
    3. **Context awareness**: Note if content is continued from/to other pages
    4. **Semantic richness**: Add multiple relevant tags per block
    5. **Traceability**: Every block must have page_number = {{ page_number }}

    PDF Page {{ page_number }}:
    {{ pdf_input }}

    Output a complete PDFPageDocument with rich metadata for this single page.
  "#
}