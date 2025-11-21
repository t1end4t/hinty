from typing import List

from baml_py import AbortController, BamlSyncStream

from hinty.core.models import AgentResponse

from ..baml_client import b
from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager


def call_router(
    user_message: str,
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> BamlSyncStream[str, str]:
    """Call the orchestrator agent with a user message and conversation history"""
    resp = b.stream.Router(
        user_message,
        conversation_history,
        baml_options={"abort_controller": controller},
    )

    return resp


def handle_router_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
    controller: AbortController,
) -> AgentResponse:
    stream = call_router(
        user_message, conversation_history, controller=controller
    )

    return AgentResponse(response=stream)
