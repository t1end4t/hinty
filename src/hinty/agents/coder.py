from pathlib import Path
from typing import AsyncGenerator, Generator, List

from baml_py import AbortController, BamlStream
from baml_py.errors import BamlAbortError
from loguru import logger

from hinty.core.models import AgentResponse

from ..baml_client.async_client import b
from ..baml_client.stream_types import CoderOutput as StreamCoderOutput
from ..baml_client.types import (
    CoderOutput,
    ConversationMessage,
    FileInfo,
)
from ..core.context_manager import ContextManager
from ..tools.file_operations import tool_read_file
from ..tools.search_and_replace import tool_apply_search_replace


def process_coder_chunk(
    chunk: CoderOutput | StreamCoderOutput | None,
) -> str:
    """Process a CoderOutput chunk into a formatted string, handling None values."""
    if chunk is None:
        return ""

    lines = []
    if chunk.summary is not None:
        lines.append(f"{chunk.summary}\n")

    if chunk.files_to_change is not None:
        for file_change in chunk.files_to_change:
            if file_change is None:
                continue
            if file_change.file_path is not None:
                lines.append(f"**File: {file_change.file_path}**\n")
            if file_change.blocks is not None:
                for block in file_change.blocks:
                    if block is None:
                        continue
                    code_block_start = (
                        f"```{block.language}"
                        if block.language is not None
                        else "```"
                    )
                    lines.append(code_block_start)
                    lines.append("<<<<<<< SEARCH")
                    if block.search is not None:
                        lines.append(block.search)
                    lines.append("=======")
                    if block.replace is not None:
                        lines.append(block.replace)
                    lines.append(">>>>>>> REPLACE")
                    lines.append("```")

            if file_change.explanation is not None:
                lines.append(f"**Explanation**: {file_change.explanation}\n")

    return "\n".join(lines)


async def call_coder(
    user_message: str,
    files: List[FileInfo],
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> BamlStream[StreamCoderOutput, CoderOutput] | None:
    """Call the coder agent with a user message, files, and conversation history"""
    try:
        resp = b.stream.Coder(
            user_message,
            files,
            conversation_history,
            baml_options={"abort_controller": controller},
        )
        return resp
    except BamlAbortError:
        logger.error("Operation was cancelled")


def prepare_files_info(
    context_manager: ContextManager,
) -> tuple[List[FileInfo], List[str]]:
    """Prepare file information and actions for the coder mode."""
    files_info = []
    actions = []
    for file_path in context_manager.get_all_files():
        relative_path = file_path.relative_to(context_manager.pwd_path)
        result = tool_read_file(file_path)
        if result.success and isinstance(result.output, str):
            file_content = result.output
            files_info.append(
                FileInfo(
                    file_path=str(relative_path), file_content=file_content
                )
            )
            logger.info(f"Add file: {file_path}")
            actions.append(f"Read file: {relative_path}")
        else:
            logger.error(f"Failed to read file {file_path}: {result.error}")
            actions.append(f"Failed to read file: {relative_path}")
    return files_info, actions


async def handle_streaming_response(
    stream: BamlStream[StreamCoderOutput, CoderOutput],
) -> AsyncGenerator[AgentResponse, None]:
    """Handle streaming the coder response."""
    async for chunk in stream:
        yield AgentResponse(response=process_coder_chunk(chunk))
    final = await stream.get_final_response()
    yield AgentResponse(response=process_coder_chunk(final))


def apply_changes(
    final: CoderOutput, context_manager: ContextManager
) -> Generator[AgentResponse, None, None]:
    """Apply search replace blocks and yield the result."""
    if final.files_to_change:
        result = tool_apply_search_replace(final, context_manager.pwd_path)
        if result.output is not None:
            files_changed = [
                str(
                    Path(r.split(" to ")[1]).relative_to(
                        context_manager.pwd_path
                    )
                )
                for r in result.output["results"]
                if "Successfully applied" in r
            ]
            yield AgentResponse(
                actions=[f"Applied changes: {', '.join(files_changed)}"]
            )
        else:
            yield AgentResponse(
                actions=[
                    f"Failed to apply changes: {result.error or 'Unknown error'}"
                ]
            )


async def handle_coder_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
    controller: AbortController,
) -> AsyncGenerator[AgentResponse, None]:
    files_info, actions = prepare_files_info(context_manager)
    yield AgentResponse(actions=actions)

    stream = await call_coder(
        user_message, files_info, conversation_history, controller
    )
    if stream:
        final = yield from handle_streaming_response(stream)

    # yield from apply_changes(final, context_manager)
