from loguru import logger
from typing import Final, Generator, List, Optional

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


def format_summary(summary: Optional[str]) -> List[str]:
    """Format the summary into a list of lines."""
    return [summary] if summary is not None else []


def format_file_path(file_path: Optional[str]) -> List[str]:
    """Format the file path into a list of lines."""
    return [f"File: {file_path}"] if file_path is not None else []


def format_explanation(explanation: Optional[str]) -> List[str]:
    """Format the explanation into a list of lines."""
    return [f"Explanation: {explanation}"] if explanation is not None else []


def format_block(block) -> List[str]:
    """Format a search-replace block into a list of lines."""
    code_block_start = f"```{block.language}" if block.language is not None else "```"
    search = block.search if block.search is not None else ""
    replace = block.replace if block.replace is not None else ""
    return [
        code_block_start,
        "<<<<<<< SEARCH",
        search,
        "=======",
        replace,
        ">>>>>>> REPLACE",
        "```"
    ]


def process_coder_chunk(
    chunk: BamlSyncStream[StreamCoderOutput, CoderOutput],
) -> BamlSyncStream[str, str]:
    """Process a CoderOutput chunk into a formatted string, handling None values."""
    logger.info("Processing coder chunk")
    if chunk is None:
        logger.info("Chunk is None, returning empty string")
        return ""
    
    summary_lines = format_summary(chunk.summary)
    file_lines = [
        line
        for file_change in (chunk.files_to_change or [])
        if file_change is not None
        for line in (
            format_file_path(file_change.file_path) +
            format_explanation(file_change.explanation) +
            [
                line
                for block in (file_change.blocks or [])
                if block is not None
                for line in format_block(block)
            ]
        )
    ]
    lines = summary_lines + file_lines
    result = "\n".join(lines)
    logger.info("Processed coder chunk")
    return result


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
    yield AgentResponse(response=process_coder_chunk(stream))
