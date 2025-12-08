from typing import AsyncGenerator

from loguru import logger
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from ..cli.theme import (
    agent_action_style,
    agent_response_style,
    agent_thinking_style,
    context_style,
)
from ..core.models import AgentResponse
from ..core.project_manager import ProjectManager


# Constants for readability
REFRESH_RATE = 10
WELCOME_MESSAGE = (
    "Welcome to the Hinty CLI! Press Enter on an empty line to quit."
)


def print_welcome(console: Console):
    """Print the welcome panel."""
    console.print(
        Panel.fit(
            WELCOME_MESSAGE,
            title="Hinty CLI",
            border_style="blue",
        )
    )


def _build_group_items(current_thinking, current_response, current_actions):
    """Build group items for live display."""
    group_items = []
    if current_thinking:
        group_items.append(
            Group(
                f"[bold {agent_thinking_style}]Thinking:[/]",
                Markdown(current_thinking),
            )
        )
    if current_response:
        group_items.append(
            Panel(
                Markdown(current_response),
                title="LLM",
                border_style=agent_response_style,
            )
        )
    if current_actions:
        group_items.append(
            f"[bold {agent_action_style}]{', '.join(current_actions)}[/]"
        )
    return group_items


def _update_state(
    partial,
    current_response,
    current_actions,
    current_thinking,
    full_response,
    console_height,
):
    """Update current state from partial response."""
    if partial.thinking:
        current_thinking = partial.thinking
    if partial.actions:
        current_actions = partial.actions
    if partial.response:
        if isinstance(partial.response, str):
            current_response = partial.response
            full_response = current_response
        else:
            for chunk in partial.response:
                full_response = chunk
                lines = chunk.split("\n")
                last_lines = lines[-console_height:]
                current_response = "\n".join(last_lines)
    return current_response, current_actions, current_thinking, full_response


def _print_final_response(
    current_thinking, current_actions, full_response, console
):
    """Print the final response after streaming."""
    if full_response:
        group_items = []
        if current_thinking:
            group_items.append(
                Group(
                    f"[bold {agent_thinking_style}]Thinking:[/]",
                    Markdown(current_thinking),
                )
            )
        if current_actions:
            group_items.append(
                f"[bold {agent_action_style}]{', '.join(current_actions)}[/]"
            )
        group_items.append(
            Panel(
                Markdown(full_response),
                title="LLM",
                border_style=agent_response_style,
            )
        )
        console.print(Group(*group_items))
        console.print()


async def display_stream_response(
    stream: AsyncGenerator[AgentResponse, None], console: Console
) -> str:
    """Display streaming response and return full response."""
    logger.info("Starting to display stream response")
    current_response = ""
    current_actions = []
    current_thinking = None
    full_response = ""
    console_height = console.height

    live = Live(
        console=console, refresh_per_second=REFRESH_RATE, transient=True
    )
    live.start()
    try:
        async for partial in stream:
            (
                current_response,
                current_actions,
                current_thinking,
                full_response,
            ) = _update_state(
                partial,
                current_response,
                current_actions,
                current_thinking,
                full_response,
                console_height,
            )
            group_items = _build_group_items(
                current_thinking, current_response, current_actions
            )
            live.update(Group(*group_items))
    except Exception as e:
        logger.error(f"Error during stream response display: {e}")
        raise
    finally:
        live.update("")
        live.stop()

    _print_final_response(
        current_thinking, current_actions, full_response, console
    )

    logger.info("Finished displaying stream response")
    return full_response


def display_files(project_manager: ProjectManager, console: Console):
    """Display files panel if the file list is not empty."""

    files_str = (
        " ".join(
            str(f.relative_to(project_manager.project_root))
            for f in project_manager.get_attached_files()
        )
        if project_manager.get_attached_files()
        else ""
    )
    if files_str:
        console.print(f"[{context_style}]Files: {files_str}[/]")
