from typing import Generator, List

from baml_py import AbortController, BamlSyncStream

from hinty.core.models import AgentResponse

from ..baml_client import b
from ..baml_client.stream_types import CoderOutput
from ..baml_client.types import (
    CoderOutput as FinalCoderOutput,
)
from ..baml_client.types import (
    ConversationMessage,
    FileInfo,
)
from ..core.context_manager import ContextManager
from ..tools.file_operations import tool_read_file
from ..tools.search_and_replace import tool_apply_search_replace


def call_coder(
    user_message: str,
    files: List[FileInfo],
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> BamlSyncStream[CoderOutput, FinalCoderOutput]:
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
        file_content = tool_read_file(file_path)
        files_info.append(
            FileInfo(file_path=str(file_path), file_content=file_content)
        )
        actions.append(f"Read_file: {file_path}")

    yield AgentResponse(actions=actions)

    stream = call_coder(
        user_message, files_info, conversation_history, controller
    )

    final = stream.get_final_response()
    response_text = (
        f"Agent will make the requested changes.\n\n"
        f"{final.diff_content}\n\n"
        f"Short explanation: {final.response}"
    )
    yield AgentResponse(response=response_text)

    success = tool_apply_search_replace(
        final.diff_content, base_path=context_manager.pwd_path
    )
    yield AgentResponse(actions=[f"Changes applied successfully: {success}"])
