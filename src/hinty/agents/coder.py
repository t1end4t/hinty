import difflib
import json
from pathlib import Path
from typing import Generator, List

from baml_py import AbortController, BamlSyncStream
from baml_py.errors import BamlAbortError
from loguru import logger

from hinty.core.models import AgentResponse

from ..baml_client import b
from ..baml_client.stream_types import CoderOutput as StreamCoderOutput
from ..baml_client.types import (
    CoderOutput,
    ConversationMessage,
    FileInfo,
    CodebaseContext,
)
from ..core.clients import get_client_registry
from ..core.project_manager import ProjectManager
from ..tools.search_and_replace import tool_search_and_replace
from ..utils.file_operations import read_content_file
from ..context.tree import get_tree
from ..context.language import get_primary_language


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


def _prepare_files_info(
    project_manager: ProjectManager,
) -> tuple[List[FileInfo], List[str]]:
    """Prepare file information and actions for the coder mode."""
    files_info = []
    actions = []
    for file_path in project_manager.get_attached_files():
        relative_path = file_path.relative_to(project_manager.project_root)
        try:
            content, file_type = read_content_file(file_path)
            if file_type == "text":
                files_info.append(
                    FileInfo(file_path=str(relative_path), file_content=content)
                )
            logger.info(f"Add file: {file_path}")
            actions.append(f"Read file: {relative_path}")
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            actions.append(f"Failed to read file: {relative_path}")
    return files_info, actions


# TODO: check it
def _handle_streaming_response(
    stream: BamlSyncStream[StreamCoderOutput, CoderOutput],
) -> Generator[AgentResponse, None, None]:
    """Handle streaming the coder response."""
    for chunk in stream:
        yield AgentResponse(response=_process_coder_chunk(chunk))
    final = stream.get_final_response()
    yield AgentResponse(response=_process_coder_chunk(final))


def _apply_changes(
    final: CoderOutput, project_manager: ProjectManager
) -> Generator[AgentResponse, None, None]:
    """Apply search replace blocks and yield the result."""
    if final.files_to_change:
        result = tool_search_and_replace(final, project_manager.project_root)
        if result.success and result.output and isinstance(result.output, str):
            output_dict = json.loads(result.output)
            files_changed = [
                str(
                    Path(r.split(" to ")[1]).relative_to(
                        project_manager.project_root
                    )
                )
                for r in output_dict["results"]
                if "Successfully applied" in r
            ]
            yield AgentResponse(
                actions=[f"Applied changes: {', '.join(files_changed)}"]
            )
        else:
            error_msg = result.error if result.error else "Unknown error"
            yield AgentResponse(
                actions=[f"Failed to apply changes: {error_msg}"]
            )


# BUG: change this
def call_coder(
    user_message: str,
    conversation_history: List[ConversationMessage],
    files: List[FileInfo],
    codebase_context: CodebaseContext,
    controller: AbortController,
) -> BamlSyncStream[StreamCoderOutput, CoderOutput] | None:
    """Call the coder agent with a user message, files, and conversation history"""
    try:
        # get client from config
        cr = get_client_registry("coder")

        resp = b.stream.Coder(
            user_message,
            conversation_history,
            files,
            codebase_context,
            baml_options={
                "abort_controller": controller,
                "client_registry": cr,
            },
        )
        return resp
    except BamlAbortError:
        logger.error("Operation was cancelled")


# def handle_coder_mode(
#     user_message: str,
#     conversation_history: List[ConversationMessage],
#     project_manager: ProjectManager,
#     controller: AbortController,
# ) -> Generator[AgentResponse, None, None]:
#     files_info, actions = _prepare_files_info(project_manager)

#     tree = get_tree(project_root=project_manager.project_root)
#     project_language = get_primary_language(
#         project_root=project_manager.project_root
#     )

#     codebase_context = CodebaseContext(
#         file_tree=tree, project_language=project_language
#     )

#     yield AgentResponse(actions=actions)

#     stream = call_coder(
#         user_message,
#         conversation_history,
#         files=files_info,
#         codebase_context,
#         controller,
#     )
#     if stream:
#         for response in _handle_streaming_response(stream):
#             yield response
#         final = stream.get_final_response()
#         for response in _apply_changes(final, project_manager):
#             yield response
