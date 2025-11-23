from typing import List

from baml_py import AbortController, BamlSyncStream

from hinty.core.models import AgentResponse

from ..baml_client import b
from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager


def call_coder(
    user_message: str,
    file_content: str,
    file_path: str,
    conversation_history: List[ConversationMessage],
    controller: AbortController,
) -> BamlSyncStream[str, str]:
    """Call the coder agent with a user message, file content, file path, and conversation history"""
    resp = b.stream.Coder(
        user_message,
        file_content,
        file_path,
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
    files = context_manager.get_all_files()
    if not files:
        raise ValueError("No files in context for coder mode")
    file_path_obj = files[0]
    file_content = file_path_obj.read_text()
    file_path = str(file_path_obj)
    stream = call_coder(
        user_message, file_content, file_path, conversation_history, controller
    )

    return AgentResponse(response=stream)
