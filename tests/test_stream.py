from typing import AsyncGenerator, List

from baml_py import AbortController
from dotenv import load_dotenv
from rich.live import Live
from rich.text import Text

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


def main():
    message = "what you can do"
    ctx = ProjectManager()
    controller = AbortController()

    stream = get_agent_response(
        user_message=message,
        conversation_history=[],
        project_manager=ctx,
        controller=controller,
    )

    for partial in stream:
        if partial.response:
            text = Text()
            with Live(text, refresh_per_second=10) as live:
                for subpartial in partial.response:
                    text.plain = subpartial
                    live.update(text)


if __name__ == "__main__":
    main()
