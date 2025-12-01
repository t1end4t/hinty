import asyncio
import time
from typing import AsyncGenerator, List
from baml_py import AbortController
from dotenv import load_dotenv
from rich.live import Live
from rich.markdown import Markdown
from hinty.agents.router import handle_smart_mode
from hinty.baml_client.types import ConversationMessage
from hinty.core.project_manager import ProjectManager
from hinty.core.models import AgentResponse

load_dotenv()


async def get_agent_response(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
    controller: AbortController,
) -> AsyncGenerator[AgentResponse, None]:
    """Get a response from the LLM"""
    async for response in handle_smart_mode(
        user_message, conversation_history, controller
    ):
        yield response


async def main():
    message = "how to be better researcher"
    ctx = ProjectManager()
    controller = AbortController()

    stream = get_agent_response(
        user_message=message,
        conversation_history=[],
        project_manager=ctx,
        controller=controller,
    )

    # Accumulate text here
    accumulated_text = ""
    subpartial_times = []
    start_time = time.time()

    # Create Live context ONCE before the loop
    with Live(
        auto_refresh=True, vertical_overflow="ellipsis", refresh_per_second=10
    ) as live:
        async for partial in stream:
            if partial.response:
                if isinstance(partial.response, str):
                    accumulated_text = partial.response
                    md = Markdown(accumulated_text)
                    live.update(md, refresh=True)
                else:
                    async for subpartial in partial.response:
                        # Accumulate the streaming text
                        accumulated_text = subpartial
                        md = Markdown(accumulated_text)
                        live.update(md, refresh=True)
                        current_time = time.time()
                        subpartial_times.append(current_time)

    # Calculate and print time differences
    print("\n=== Subpartial Timing Analysis ===")
    print(f"Total subpartials: {len(subpartial_times)}")
    
    if subpartial_times:
        print(f"First subpartial at: {subpartial_times[0] - start_time:.4f}s")
        print(f"Last subpartial at: {subpartial_times[-1] - start_time:.4f}s")
        print(f"Total duration: {subpartial_times[-1] - subpartial_times[0]:.4f}s")
        
        print("\nTime between subpartials:")
        for i in range(1, len(subpartial_times)):
            delta = subpartial_times[i] - subpartial_times[i-1]
            print(f"  Subpartial {i}: {delta:.4f}s")


if __name__ == "__main__":
    asyncio.run(main())
