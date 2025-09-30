from typing import List

from ..agents import (
    call_router,
)
from ..baml_client.types import ConversationMessage
from .context_manager import ProjectContext
from .models import Mode


def get_agent_response(
    user_message: str,
    conversation_history: List[ConversationMessage],
    mode: Mode,
    context_manager: ProjectContext,
) -> str:
    """Get a response from the LLM"""
    if mode == Mode.ROUTER:
        response = call_router(user_message, conversation_history)

    return response
