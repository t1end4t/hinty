from loguru import logger
from typing import Generator, List

from baml_py import AbortController, BamlSyncStream

from hinty.core.models import AgentResponse

from ..baml_client import b
from ..baml_client.stream_types import CoderOutput as StreamCoderOutput
from ..baml_client.types import (
    CoderOutput,
)
from ..baml_client.types import (
    ConversationMessage,
    FileInfo,
)
from ..core.context_manager import ContextManager
from ..tools.file_operations import tool_read_file
from ..tools.search_and_replace import tool_apply_search_replace


def process_coder_chunk(chunk: StreamCoderOutput) -> str:
    """Process a CoderOutput chunk into a formatted string, handling None values."""
    if chunk is None:
        return ""

    lines = []
    if chunk.summary is not None:
        lines.append(chunk.summary)

    if chunk.files_to_change is not None:
        for file_change in chunk.files_to_change:
            if file_change is None:
                continue
            if file_change.file_path is not None:
                lines.append(f"File: {file_change.file_path}")
            if file_change.explanation is not None:
                lines.append(f"Explanation: {file_change.explanation}")
            if file_change.blocks is not None:
                for block in file_change.blocks:
                    if block is None:
                        continue
                    if block.language is not None:
                        lines.append(f"```{block.language}")
                    else:
                        lines.append("```")
                    lines.append("<<<<<<< SEARCH")
                    if block.search is not None:
                        lines.append(block.search)
                    lines.append("=======")
                    if block.replace is not None:
                        lines.append(block.replace)
                    lines.append(">>>>>>> REPLACE")
                    lines.append("```")

    return "\n".join(lines)


def call_coder(
    user_message: str,
    files: List[FileInfo],
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> BamlSyncStream[StreamCoderOutput, CoderOutput]:
    """Call the coder agent with a user message, files, and conversation history"""
    resp = b.stream.Coder(
        user_message,
        files,
        conversation_history,
        baml_options={"abort_controller": controller},
    )

    return resp


def handle_coder_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
    controller: AbortController,
) -> Generator[AgentResponse, None, None]:
    files_info = []
    actions = []
    for file_path in context_manager.get_all_files():
        result = tool_read_file(file_path)
        if result.success and isinstance(result.output, str):
            file_content = result.output
            relative_path = file_path.relative_to(context_manager.pwd_path)
            files_info.append(
                FileInfo(
                    file_path=str(relative_path), file_content=file_content
                )
            )
            logger.info(f"Add file: {file_path}")
            actions.append(f"Read_file: {file_path}")
        else:
            logger.error(f"Failed to read file {file_path}: {result.error}")
            actions.append(f"Failed to read file: {file_path}")

    yield AgentResponse(actions=actions)

    stream = call_coder(
        user_message, files_info, conversation_history, controller
    )

    # BUG: should stream, not get final
    # final = stream.get_final_response()
    # response_text = process_coder_response(final)
    for chunk in stream:
        current_resp = process_coder_chunk(chunk)
        yield AgentResponse(response=current_resp)

    # result = tool_apply_search_replace(final, context_manager.pwd_path)
    # if result.success:
    #     yield AgentResponse(
    #         actions=[f"Changes applied successfully: {result.output}"]
    #     )
    # else:
    #     yield AgentResponse(
    #         actions=[f"Failed to apply changes: {result.error}"]
    #     )
