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

    stream = get_agent_response(
        user_message=message,
        conversation_history=[],
        project_manager=ctx,
        controller=controller,
    )

    # Print response
    previous_content = ""
    async for partial in stream:
        if partial.response:
            if isinstance(partial.response, str):
                pass
            else:
                async for subpartial in partial.response:
                    # Find the last newline in previous content
                    last_newline_pos = previous_content.rfind("\n")

                    # Find the last newline in current content
                    current_newline_pos = subpartial.rfind("\n")

                    # If we have a new complete line
                    if current_newline_pos > last_newline_pos:
                        # Extract from after the last newline in previous to current newline
                        start_pos = (
                            last_newline_pos + 1 if last_newline_pos >= 0 else 0
                        )
                        line_content = subpartial[
                            start_pos : current_newline_pos + 1
                        ]
                        md = Markdown(line_content)
                        console.print(md)

                    previous_content = subpartial


if __name__ == "__main__":
    asyncio.run(main())
