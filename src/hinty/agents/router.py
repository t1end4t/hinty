from typing import AsyncGenerator, List

from baml_py import AbortController, BamlStream
from baml_py.errors import BamlAbortError
from loguru import logger

from hinty.core.models import AgentResponse

from ..baml_client.async_client import b
from ..baml_client.types import ConversationMessage


async def _call_router(
    user_message: str,
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> BamlStream[str, str] | None:
    """Call the orchestrator agent with a user message and conversation history"""
    try:
        resp = b.stream.Router(
            user_message,
            conversation_history,
            baml_options={"abort_controller": controller},
        )
        return resp
    except BamlAbortError:
        logger.error("Operation was cancelled")


async def handle_smart_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> AsyncGenerator[AgentResponse, None]:
    stream = await _call_router(
        user_message, conversation_history, controller=controller
    )
    yield AgentResponse(response=stream)

    # get final response
    if stream:
        final = await stream.get_final_response()
        yield AgentResponse(response=final)
