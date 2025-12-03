from typing import Generator, List

from baml_py import AbortController, BamlSyncStream
from baml_py.errors import BamlAbortError
from loguru import logger

from hinty.core.models import AgentResponse

from ..baml_client import b
from ..baml_client.types import ConversationMessage, ChatResponse
from ..baml_client.stream_types import ChatResponse as StreamChatResponse


def call_chatgpt(
    user_message: str,
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> BamlSyncStream[StreamChatResponse, ChatResponse] | None:
    """Call the orchestrator agent with a user message and conversation history"""
    try:
        resp = b.stream.ChatGPT(
            user_message,
            conversation_history,
            baml_options={"abort_controller": controller},
        )
        return resp
    except BamlAbortError:
        logger.error("Operation was cancelled")


def handle_chatgpt_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> Generator[AgentResponse, None, None]:
    stream = call_chatgpt(
        user_message, conversation_history, controller=controller
    )
    yield AgentResponse(response=stream)

    # get final response
    if stream:
        final = stream.get_final_response()
        yield AgentResponse(response=final)
