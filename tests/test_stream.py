import asyncio
from typing import AsyncGenerator, List

from baml_py import AbortController
from dotenv import load_dotenv
from rich.live import Live
from rich.markdown import Markdown

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

    stream = get_agent_response(
        user_message=message,
        conversation_history=[],
        project_manager=ctx,
        controller=controller,
    )

    async for partial in stream:
        if partial.response:
            with Live(auto_refresh=False) as live:
                if isinstance(partial.response, str):
                    md = Markdown(partial.response)
                    live.update(md)
                else:
                    responses = []
                    async for subpartial in partial.response:
                        responses.append(subpartial)
                        full_text = "".join(responses)
                        md = Markdown(full_text)
                        live.update(md)


if __name__ == "__main__":
    asyncio.run(main())
