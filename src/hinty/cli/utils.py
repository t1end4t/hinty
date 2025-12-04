from typing import AsyncGenerator

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
from ..core.project_manager import ProjectManager
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


async def display_stream_response(
    stream: AsyncGenerator[AgentResponse, None], console: Console
) -> str:
    """Display streaming response and return full response."""
    current_response = ""
    current_actions = []
    current_thinking = None
    full_response = ""
    console_height = console.height

    live = Live(
        console=console,
        refresh_per_second=REFRESH_RATE,
    )
    live.start()
    async for partial in stream:
        # show thinking
        if partial.thinking:
            current_thinking = partial.thinking

        # show actions
        if partial.actions:
            current_actions = partial.actions

        # accumulate and show response
        if partial.response:
            if isinstance(partial.response, str):
                current_response = partial.response
                full_response = current_response
            else:
                # Handle stream case by consuming chunks
                for chunk in partial.response:
                    full_response = chunk
                    # Split into lines and take only the last N lines
                    lines = chunk.split("\n")
                    last_lines = lines[-console_height:]
                    current_response = "\n".join(last_lines)

            # Update live display with truncated response
            group_items = []
            if current_thinking:
                group_items.append(
                    Group(
                        f"[bold {agent_thinking_style}]Thinking:[/]",
                        Markdown(current_thinking),
                    )
                )
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
            live.update(Group(*group_items))
        else:
            # No response, but update for actions
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
            live.update(Group(*group_items))

    # Clear the live display before stopping
    live.update("")
    live.stop()

    # Print final response normally (cursor stays at bottom)
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

        # NOTE: in final response, show thinking and action before response
        group_items.append(
            Panel(
                Markdown(full_response),
                title="LLM",
                border_style=agent_response_style,
            )
        )
        console.print(Group(*group_items))
        # add new line
        console.print()

    return full_response


def display_files(project_manager: ProjectManager):
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


def get_user_input(
    session: PromptSession, project_manager: ProjectManager
) -> str:
    """Prompt for and return user input."""

    prompt_text = f"{project_manager.mode.value} >> "
    return session.prompt(
        prompt_text,
        style=catppuccin_mocha_style,
    )
