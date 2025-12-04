from typing import AsyncGenerator, List

from baml_py import AbortController, BamlSyncStream
from baml_py.errors import BamlAbortError
from loguru import logger

from hinty.core.models import AgentResponse

from ..baml_client import b
from ..baml_client.stream_types import ChatGPTOutput as StreamChatGPTOutput
from ..baml_client.types import (
    ChatGPTOutput,
    ConversationMessage,
    FetchUrlTool,
    SearchWebTool,
)
from ..core.models import ChatgptTool
from ..tools.fetch_url import tool_fetch_url
from ..tools.search_web import tool_search_web


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


async def execute_tool(tool_call: ChatgptTool) -> dict[str, str] | None:
    if isinstance(tool_call, FetchUrlTool):
        result = await tool_fetch_url(tool_call.url)
        if result.success:
            return {"name": "fetch_url", "output": str(result.output)}
        else:
            return None
    elif isinstance(tool_call, SearchWebTool):
        result = await tool_search_web(tool_call.query)
        if result.success:
            return {"name": "search_web", "output": str(result.output)}
        else:
            return None
    else:
        return None


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
        tool_name = (
            "fetch_url"
            if isinstance(final_response.tool_call, FetchUrlTool)
            else "search_web"
        )
        input_param = (
            final_response.tool_call.url
            if isinstance(final_response.tool_call, FetchUrlTool)
            else final_response.tool_call.query
        )
        yield AgentResponse(
            actions=[
                f"Executing {tool_name} with {'url' if isinstance(final_response.tool_call, FetchUrlTool) else 'query'}: {input_param}"
            ]
        )
        tool_result = await execute_tool(final_response.tool_call)
        if tool_result is None:
            break
