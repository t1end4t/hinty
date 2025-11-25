from typing import Generator, List

from baml_py import AbortController

from ..agents.router import handle_smart_mode
from ..agents.coder import handle_coder_mode
from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager
from ..core.models import AgentResponse, Mode


def get_agent_response(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
    controller: AbortController,
) -> Generator[AgentResponse, None, None]:
    """Get a response from the LLM"""
    if context_manager.current_mode == Mode.SMART:
        yield from handle_smart_mode(
            user_message, conversation_history, context_manager, controller
        )
    elif context_manager.current_mode == Mode.CODER:
        yield from handle_coder_mode(
            user_message, conversation_history, context_manager, controller
        )
    else:
        yield AgentResponse(
            response=f"Mode {context_manager.current_mode} not yet implemented"
        )
