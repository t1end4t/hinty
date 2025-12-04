from typing import AsyncGenerator, List

from baml_py import AbortController, BamlSyncStream
from baml_py.errors import BamlAbortError
from loguru import logger

from hinty.core.models import AgentResponse

from ..baml_client import b
from ..baml_client.stream_types import ChatGPTOutput as StreamChatGPTOutput
from ..baml_client.types import ChatGPTOutput, ConversationMessage
from ..baml_client.types import SearchWebTool, FetchUrlTool

from ..tools.fetch_url import tool_fetch_url
from ..tools.search_web import tool_search_web
from ..tools.write_file import tool_write_file


def call_chatgpt(
    user_message: str,
    conversation_history: List[ConversationMessage],
    tool_result: dict[str, str] | None,
    controller: AbortController,
) -> BamlSyncStream[StreamChatGPTOutput, ChatGPTOutput] | None:
    """Call the orchestrator agent with a user message and conversation history"""
    try:
        resp = b.stream.ChatGPT(
            user_message,
            conversation_history,
            tool_result,
            baml_options={"abort_controller": controller},
        )
        return resp
    except BamlAbortError:
        logger.error("Operation was cancelled")


async def handle_chatgpt_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> AsyncGenerator[AgentResponse, None]:
    tool_result = None
    while True:
        stream = call_chatgpt(
            user_message,
            conversation_history,
            tool_result,
            controller,
        )
        if not stream:
            break
        for chunk in stream:
            yield AgentResponse(response=chunk.response)
        final_response = stream.get_final_response()
        yield AgentResponse(response=final_response.response)
        if final_response.tool_call is None:
            break
        # Execute tool and prepare result for next iteration
        if isinstance(final_response.tool_call, FetchUrlTool):
            tool_result = await tool_fetch_url(final_response.tool_call)
        elif isinstance(final_response.tool_call, SearchWebTool):
            tool_result = await tool_search_web(final_response.tool_call)
        else:
            break  # Unknown tool, stop
