import asyncio
from typing import AsyncGenerator, List
from baml_py import AbortController
from dotenv import load_dotenv
from rich.markdown import Markdown
from rich.console import Console
from hinty.agents.router import handle_smart_mode
from hinty.baml_client.types import ConversationMessage
from hinty.core.project_manager import ProjectManager
from hinty.core.models import AgentResponse

load_dotenv()


async def get_agent_response(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
    controller: AbortController,
) -> AsyncGenerator[AgentResponse, None]:
    """Get a response from the LLM"""
    async for response in handle_smart_mode(
        user_message, conversation_history, controller
    ):
        yield response


async def main():
    message = "how to be better researcher"
    ctx = ProjectManager()
    controller = AbortController()

    console = Console()
    accumulated_text = ""

    stream = get_agent_response(
        user_message=message,
        conversation_history=[],
        project_manager=ctx,
        controller=controller,
    )

    # Print response
    async for partial in stream:
        if partial.response:
            if isinstance(partial.response, str):
                accumulated_text = partial.response
                md = Markdown(accumulated_text)
                console.print(md)
            else:
                async for subpartial in partial.response:
                    new_content = subpartial[len(accumulated_text) :]
                    accumulated_text = subpartial
                    md = Markdown(new_content)
                    console.print(md)


if __name__ == "__main__":
    asyncio.run(main())
