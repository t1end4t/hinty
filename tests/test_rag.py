from pathlib import Path

from dotenv import load_dotenv

from hinty.core.project_manager import ProjectManager
from hinty.tools.rag import tool_rag

load_dotenv()


def main():
    """Run a simple test of the RAG tool."""
    query = "What is the main topic of this document?"
    pdf_path = Path("tests/test.pdf")  # Replace with actual PDF path

    ctx = ProjectManager()

    result = tool_rag(query=query, pdf_path=pdf_path, project_manager=ctx)

    print("RAG Tool Result:")
    print(result)


if __name__ == "__main__":
    main()
