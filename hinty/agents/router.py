from typing import List
from baml_py import BamlSyncStream

from hinty.core.models import AgentResponse

from ..baml_client import b
from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager


def call_router(
    user_message: str, conversation_history: List[ConversationMessage]
) -> BamlSyncStream[str, str]:
    """Call the orchestrator agent with a user message and conversation history"""
    resp = b.stream.Router(user_message, conversation_history)

    return resp


def handle_router_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
) -> AgentResponse:
    resp = call_router(user_message, conversation_history)

    return AgentResponse(response=resp)
