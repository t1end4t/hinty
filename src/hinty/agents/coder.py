import mimetypes
from typing import List

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
) -> AgentResponse:
    files_info = []
    for file_path in context_manager.get_all_files():
        file_content = tool_read_file(file_path)
        files_info.append(FileInfo(file_path=str(file_path), file_content=file_content))
    
    stream = call_coder(
        user_message, files_info, conversation_history, controller
    )

    return AgentResponse(response=stream)
