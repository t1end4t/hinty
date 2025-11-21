from typing import AsyncIterator, List

from loguru import logger

from ..agents.router import handle_router_mode
from ..baml_client import b
from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager
from ..core.models import AgentResponse, Mode


async def get_agent_response(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
) -> AsyncIterator[str]:
    """Get a streaming response from the LLM based on the current mode."""
    logger.debug(f"Getting agent response for mode: {context_manager.current_mode}")
    try:
        if context_manager.current_mode == Mode.ROUTER:
            # For router mode, use the existing streaming BAML call
            stream = b.stream.Router(
                user_message, conversation_history=conversation_history
            )
            async for partial in stream:
                yield str(partial)
        else:
            # For other modes, simulate streaming by yielding the response once
            response = AgentResponse(
                response=f"Mode {context_manager.current_mode} not yet implemented"
            )
            yield response.response
        logger.debug("Agent response stream completed")
    except Exception as e:
        logger.error(f"Error in get_agent_response: {e}")
        raise
