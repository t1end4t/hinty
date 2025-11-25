import asyncio
from typing import AsyncGenerator

from baml_py import BamlSyncStream
from prompt_toolkit import PromptSession
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from ..cli.theme import (
    agent_action_style,
    agent_response_style,
    agent_thinking_style,
    catppuccin_mocha_style,
    context_style,
)
from ..core.context_manager import ContextManager
from ..core.models import AgentResponse

console = Console()

# Constants for readability
REFRESH_RATE = 10
WELCOME_MESSAGE = (
    "Welcome to the Hinty CLI! Press Enter on an empty line to quit."
)


def print_welcome():
    """Print the welcome panel."""
    console.print(
        Panel.fit(
            WELCOME_MESSAGE,
            title="Hinty CLI",
            border_style="blue",
        )
    )


def _display_with_live(
    generator: BamlSyncStream[str, str], console: Console
) -> str:
    """Helper to display a generator of strings with live updates."""
    full_response = ""
    with Live(console=console, refresh_per_second=REFRESH_RATE) as live:
        for chunk in generator:
            full_response = chunk
            live.update(
                Panel(
                    Markdown(full_response),
                    title="LLM",
                    border_style=agent_response_style,
                )
            )
    console.print()  # Newline for separation
    return full_response


def display_response(
    response: str | BamlSyncStream[str, str], console: Console
) -> str:
    """Display response with live updating and return full response."""
    if isinstance(response, str):
        console.print(
            Panel(
                Markdown(response),
                title="LLM",
                border_style=agent_response_style,
            )
        )
        return response
    else:
        return _display_with_live(response, console)


async def display_stream_response(
    stream: AsyncGenerator[AgentResponse, None], console: Console
) -> str:
    """Display streaming response and return full response."""
    current_response = ""
    current_actions = ""
    current_thinking = None
    full_response = ""

    live = Live(console=console, refresh_per_second=REFRESH_RATE)
    try:
        live.start()
        async for partial in stream:
            # show thinking
            if partial.thinking:
                current_thinking = Group(
                    f"[bold {agent_thinking_style}]Thinking:[/]",
                    Markdown(partial.thinking),
                )

            # show actions
            if partial.actions:
                current_actions = f"[bold {agent_action_style}]{', '.join(partial.actions)}[/]"

            # accumulate and show response
            if partial.response:
                if isinstance(partial.response, str):
                    current_response = partial.response
                    full_response = current_response
                    group_items = [
                        Panel(
                            Markdown(current_response),
                            title="LLM",
                            border_style=agent_response_style,
                        ),
                        current_actions,
                    ]
                    if current_thinking:
                        group_items.insert(0, current_thinking)
                    live.update(Group(*group_items))
                else:
                    # Handle stream case by consuming chunks
                    try:
                        async for chunk in partial.response:
                            current_response = chunk
                            full_response = current_response
                            group_items = [
                                Panel(
                                    Markdown(current_response),
                                    title="LLM",
                                    border_style=agent_response_style,
                                ),
                                current_actions,
                            ]
                            if current_thinking:
                                group_items.insert(0, current_thinking)
                            live.update(Group(*group_items))
                    except KeyboardInterrupt:
                        continue
            else:
                # No response, but update for actions
                group_items = [
                    Panel(
                        Markdown(current_response),
                        title="LLM",
                        border_style=agent_response_style,
                    ),
                    current_actions,
                ]
                if current_thinking:
                    group_items.append(current_thinking)
                live.update(Group(*group_items))
    except KeyboardInterrupt:
        from loguru import logger

        logger.warning("Stream display interrupted by user")
    except Exception as e:
        from loguru import logger

        logger.error(f"Error during streaming: {e}")
    finally:
        live.stop()
        console.print()  # Newline for separation

    return full_response


def display_files(context_manager: ContextManager):
    """Display files panel if the file list is not empty."""
    files_str = (
        " ".join(
            str(f.relative_to(context_manager.pwd_path))
            for f in context_manager.get_all_files()
        )
        if context_manager.get_all_files()
        else ""
    )
    if files_str:
        console.print(f"[{context_style}]Files: {files_str}[/]")


async def get_user_input(
    session: PromptSession, context_manager: ContextManager
) -> str:
    """Prompt for and return user input."""

    prompt_text = f"{context_manager.current_mode.value} >> "
    return await asyncio.to_thread(
        session.prompt,
        prompt_text,
        style=catppuccin_mocha_style,
    )
