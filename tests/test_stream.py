from typing import Generator, List

from baml_py import AbortController
from dotenv import load_dotenv
from rich.live import Live
from rich.text import Text

from hinty.agents.router import handle_smart_mode
from hinty.baml_client.types import ConversationMessage
from hinty.core.context_manager import ContextManager
from hinty.core.models import AgentResponse

load_dotenv()


def get_agent_response(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
    controller: AbortController,
) -> Generator[AgentResponse, None, None]:
    """Get a response from the LLM"""
    yield handle_smart_mode(
        user_message, conversation_history, context_manager, controller
    )


def main():
    message = "what you can do"
    ctx = ContextManager()
    controller = AbortController()

    # stream = handle_smart_mode(
    #     user_message=message,
    #     conversation_history=[],
    #     context_manager=ctx,
    #     controller=controller,
    # )
    stream = get_agent_response(
        user_message=message,
        conversation_history=[],
        context_manager=ctx,
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
