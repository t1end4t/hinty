from typing import List, AsyncGenerator

from baml_py import AbortController, BamlStream

from hinty.core.models import AgentResponse

from ..baml_client.async_client import b
from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager


async def call_router(
    user_message: str,
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> BamlStream[str, str]:
    """Call the orchestrator agent with a user message and conversation history"""
    resp = b.stream.Router(
        user_message,
        conversation_history,
        baml_options={"abort_controller": controller},
    )

    return resp


async def handle_smart_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
    controller: AbortController,
) -> AsyncGenerator[AgentResponse, None]:
    stream = await call_router(
        user_message, conversation_history, controller=controller
    )

    try:
        yield AgentResponse(response=stream)

        # get final response
        final = await stream.get_final_response()
        yield AgentResponse(response=final)
    except KeyboardInterrupt:
        controller.abort()
        raise
