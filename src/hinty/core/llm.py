from typing import AsyncGenerator, List
  
from baml_py import AbortController
  
from ..agents.chatgpt import handle_chatgpt_mode
from ..agents.coder import handle_coder_mode
from ..baml_client.types import ConversationMessage
from ..core.project_manager import ProjectManager
from ..core.models import AgentResponse, Mode
  
  
async def get_agent_response(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
    controller: AbortController,
) -> AsyncGenerator[AgentResponse, None]:
    """Get a response from the LLM"""
    if project_manager.mode == Mode.CHATGPT:
        async for item in handle_chatgpt_mode(
            user_message, conversation_history, controller
        ):
            yield item
    # elif project_manager.mode == Mode.CODER:
    #     async for item in handle_coder_mode(
    #         user_message, conversation_history, controller
    #     ):
    #         yield item
    else:
        yield AgentResponse(
            response=f"Mode {project_manager.mode} not yet implemented"
        )
