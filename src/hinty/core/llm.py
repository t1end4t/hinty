from typing import AsyncGenerator, List

from baml_py import AbortController

from ..agents.router import handle_smart_mode
from ..agents.coder import handle_coder_mode
from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager
from ..core.models import AgentResponse, Mode


async def get_agent_response(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
    controller: AbortController,
) -> AsyncGenerator[AgentResponse, None]:
    """Get a response from the LLM"""
    if context_manager.current_mode == Mode.SMART:
        async for response in handle_smart_mode(
            user_message, conversation_history, context_manager, controller
        ):
            yield response
    elif context_manager.current_mode == Mode.CODER:
        async for response in handle_coder_mode(
            user_message, conversation_history, context_manager, controller
        ):
            yield response
    else:
        yield AgentResponse(
            response=f"Mode {context_manager.current_mode} not yet implemented"
        )
