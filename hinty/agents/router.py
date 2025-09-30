from typing import List

from ..baml_client.sync_client import b
from ..baml_client.types import ConversationMessage


def call_router(
    user_message: str, conversation_history: List[ConversationMessage]
) -> str:
    """
    Router agent that determines user intent and routes to appropriate agent.

    Returns the response from the determined agent based on intent.
    """
    router_response = b.Router(user_message, conversation_history)

    return router_response
