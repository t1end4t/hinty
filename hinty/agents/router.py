from typing import List

from ..baml_client import b
from ..baml_client.types import ConversationMessage


def call_orchestrator(
    user_message: str, conversation_history: List[ConversationMessage]
) -> str:
    """Call the orchestrator agent with a user message and conversation history"""
    resp = b.Orchestrator(user_message, conversation_history)

    return resp
