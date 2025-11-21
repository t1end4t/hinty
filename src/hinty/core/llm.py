from typing import List

from ..agents.router import handle_router_mode
from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager
from ..core.models import AgentResponse, Mode


def get_agent_response(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
) -> AgentResponse:
    """Get a response from the LLM"""
    if context_manager.current_mode == Mode.ROUTER:
        return handle_router_mode(
            user_message, conversation_history, context_manager
        )
    else:
        return AgentResponse(
            response=f"Mode {context_manager.current_mode} not yet implemented"
        )
