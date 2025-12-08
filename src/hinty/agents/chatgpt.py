from typing import AsyncGenerator, Dict, List

from baml_py import AbortController, BamlSyncStream, Collector, Image, Pdf
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
    ToolResult,
)
from ..core.clients import get_client_registry
from ..core.models import ChatgptTool
from ..tools.fetch_url import tool_fetch_url
from ..tools.search_web import tool_search_web
from ..utils.file_operations import read_content_file
from ..core.project_manager import ProjectManager


def call_chatgpt(
    user_message: str,
    conversation_history: List[ConversationMessage],
    additional_files: List[Dict[str, str]] | None,
    additional_images: List[Image] | None,
    additional_docs: List[Pdf] | None,
    tool_result: ToolResult | None,
    controller: AbortController,
) -> BamlSyncStream[StreamChatGPTOutput, ChatGPTOutput] | None:
    """Call the orchestrator agent with a user message and conversation history"""
    try:
        # get client from config
        cr = get_client_registry("chatgpt")

        resp = b.stream.ChatGPT(
            user_message,
            conversation_history,
            additional_files=additional_files,
            additional_images=additional_images,
            additional_docs=additional_docs,
            tool_result=tool_result,
            baml_options={
                "abort_controller": controller,
                "client_registry": cr,
            },
        )
        return resp
    except BamlAbortError:
        logger.error("Operation was cancelled")


async def execute_tool(tool_call: ChatgptTool) -> ToolResult | None:
    if isinstance(tool_call, FetchUrlTool):
        result = await tool_fetch_url(tool_call.url)
        return ToolResult(
            name="fetch_url",
            success=result.success,
            output=str(result.output) if result.success else None,
            error=result.error if not result.success else None,
        )
    elif isinstance(tool_call, SearchWebTool):
        result = await tool_search_web(tool_call.query)
        return ToolResult(
            name="search_web",
            success=result.success,
            output=str(result.output) if result.success else None,
            error=result.error if not result.success else None,
        )
    else:
        return None


def get_tool_info(tool_call: ChatgptTool) -> tuple[str, str, str]:
    """Get tool name, parameter name, and input value for display."""
    if isinstance(tool_call, FetchUrlTool):
        return "fetch_url", "url", tool_call.url
    elif isinstance(tool_call, SearchWebTool):
        return "search_web", "query", tool_call.query
    else:
        return "unknown_tool", "input", str(tool_call)


async def handle_chatgpt_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
    controller: AbortController,
) -> AsyncGenerator[AgentResponse, None]:
    # track token
    chatgpt_collector = Collector(name="chatgpt_collector")

    # Read additional files
    additional_files = []
    additional_images = []
    additional_docs = []
    for file_path in project_manager.get_attached_files():
        try:
            content, file_type = read_content_file(file_path)
            if file_type == "text":
                additional_files.append(
                    {"file_path": str(file_path), "content": content}
                )
            elif file_type == "pdf":
                additional_docs.append(Pdf(uri=content))
            # Skip images for now
        except Exception as e:
            logger.error(f"Error reading attached file {file_path}: {e}")

    tool_result = None

    while True:
        stream = call_chatgpt(
            user_message,
            conversation_history,
            additional_files,
            additional_images,
            additional_docs,
            tool_result,
            controller,
        )
        if not stream:
            break
        for chunk in stream:
            yield AgentResponse(response=chunk.response)
        final_response = stream.get_final_response()
        yield AgentResponse(response=final_response.response)
        if chatgpt_collector.last:
            logger.info(f"ChatGPT mode usage: {chatgpt_collector.last.usage}")

        if final_response.tool_call is None:
            break
        # Execute tool and prepare result for next iteration
        tool_name, param_name, input_param = get_tool_info(
            final_response.tool_call
        )
        yield AgentResponse(
            actions=[f"Executing {tool_name} with {param_name}: {input_param}"]
        )
        tool_result = await execute_tool(final_response.tool_call)
        if tool_result is None or not tool_result.success:
            break
        yield AgentResponse(actions=[f"Executed {tool_name}"])
