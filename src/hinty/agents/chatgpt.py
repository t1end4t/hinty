from typing import Generator, List

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


def handle_chatgpt_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> Generator[AgentResponse, None, None]:
    first_stream = call_chatgpt(
        user_message,
        conversation_history,
        tool_result=None,
        controller=controller,
    )

    if first_stream:
        for chunk in first_stream:
            yield AgentResponse(response=chunk.response)

        # return final response for user
        router_decision = first_stream.get_final_response()
        yield AgentResponse(response=router_decision.response)

        # run tool function to get input
        if isinstance(router_decision.tool_call, FetchUrlTool):
            pass
        elif isinstance(router_decision.tool_call, SearchWebTool):
            pass
