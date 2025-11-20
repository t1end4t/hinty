from typing import List
import time
from loguru import logger

from hinty.core.models import AgentResponse

from ..baml_client import b
from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager


def call_router(
    user_message: str, conversation_history: List[ConversationMessage]
):
    """Call the orchestrator agent with a user message and conversation history"""
    resp = b.stream.Router(user_message, conversation_history)

    return resp


def handle_router_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
) -> AgentResponse:
    start_time = time.time()
    stream = call_router(user_message, conversation_history)

    previous = ""
    full_response = ""

    for partial in stream:
        current = str(partial)
        new_content = current[len(previous) :]
        full_response += new_content
        previous = current

    total_time = time.time() - start_time
    logger.info(f"Router response time: {total_time:.3f}s")

    return AgentResponse(response=full_response)
