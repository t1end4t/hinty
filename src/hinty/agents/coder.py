import difflib
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
from ..core.project_manager import ProjectManager
from ..utils import apply_search_replace, read_content_file


def _format_diff_block(search: str, replace: str) -> List[str]:
    """Format search/replace as a unified diff showing only changes."""
    search_lines = search.splitlines()
    replace_lines = replace.splitlines()

    diff_lines = []
    matcher = difflib.SequenceMatcher(None, search_lines, replace_lines)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in search_lines[i1:i2]:
                diff_lines.append(f"  {line}")
        elif tag == "replace":
            for line in search_lines[i1:i2]:
                diff_lines.append(f"- {line}")
            for line in replace_lines[j1:j2]:
                diff_lines.append(f"+ {line}")
        elif tag == "delete":
            for line in search_lines[i1:i2]:
                diff_lines.append(f"- {line}")
        elif tag == "insert":
            for line in replace_lines[j1:j2]:
                diff_lines.append(f"+ {line}")

    return diff_lines


def _process_coder_chunk(
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

                    if block.search is not None and block.replace is not None:
                        diff_lines = _format_diff_block(
                            block.search, block.replace
                        )
                        lines.extend(diff_lines)
                    elif block.search is not None:
                        search_lines = block.search.splitlines()
                        for line in search_lines:
                            lines.append(f"- {line}")
                    elif block.replace is not None:
                        replace_lines = block.replace.splitlines()
                        for line in replace_lines:
                            lines.append(f"+ {line}")

                    lines.append("```")

            if file_change.explanation is not None:
                lines.append(f"**Explanation**: {file_change.explanation}\n")

    return "\n".join(lines)


async def _call_coder(
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


def _prepare_files_info(
    project_manager: ProjectManager,
) -> tuple[List[FileInfo], List[str]]:
    """Prepare file information and actions for the coder mode."""
    files_info = []
    actions = []
    for file_path in project_manager.get_attached_files():
        relative_path = file_path.relative_to(project_manager.project_root)
        try:
            file_content = read_content_file(file_path)
            files_info.append(
                FileInfo(
                    file_path=str(relative_path), file_content=file_content
                )
            )
            logger.info(f"Add file: {file_path}")
            actions.append(f"Read file: {relative_path}")
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            actions.append(f"Failed to read file: {relative_path}")
    return files_info, actions


async def _handle_streaming_response(
    stream: BamlStream[StreamCoderOutput, CoderOutput],
) -> AsyncGenerator[AgentResponse, None]:
    """Handle streaming the coder response."""
    async for chunk in stream:
        yield AgentResponse(response=_process_coder_chunk(chunk))
    final = await stream.get_final_response()
    yield AgentResponse(response=_process_coder_chunk(final))


def _apply_changes(
    final: CoderOutput, project_manager: ProjectManager
) -> Generator[AgentResponse, None, None]:
    """Apply search replace blocks and yield the result."""
    if final.files_to_change:
        try:
            output = apply_search_replace(final, project_manager.project_root)
            files_changed = [
                str(
                    Path(r.split(" to ")[1]).relative_to(
                        project_manager.project_root
                    )
                )
                for r in output["results"]
                if "Successfully applied" in r
            ]
            yield AgentResponse(
                actions=[f"Applied changes: {', '.join(files_changed)}"]
            )
        except ValueError as e:
            yield AgentResponse(actions=[f"Failed to apply changes: {e}"])


async def handle_coder_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
    controller: AbortController,
) -> AsyncGenerator[AgentResponse, None]:
    files_info, actions = _prepare_files_info(project_manager)

    yield AgentResponse(actions=actions)

    stream = await _call_coder(
        user_message, files_info, conversation_history, controller
    )
    if stream:
        async for response in _handle_streaming_response(stream):
            yield response
        final = await stream.get_final_response()
        for response in _apply_changes(final, project_manager):
            yield response
