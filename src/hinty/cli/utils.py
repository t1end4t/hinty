from typing import Generator

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from prompt_toolkit import PromptSession

from ..cli.theme import (
    agent_response_style,
    context_style,
    agent_thinking_style,
    agent_action_style,
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


def display_actions(actions: list[str], console: Console):
    """Display actions with a specific theme."""
    if actions:
        console.print(
            Panel(
                ", ".join(actions),
                title="Actions",
                border_style=agent_action_style,
            )
        )


def display_thinking(thinking: str, console: Console):
    """Display thinking with a specific theme."""
    if thinking:
        console.print(
            Panel(
                Markdown(thinking),
                title="Thinking",
                border_style=agent_thinking_style,
            )
        )


def display_response(
    response: str | Generator[str, None, None], console: Console
) -> str:
    """Display response with live updating and return full response."""
    full_response = ""
    if isinstance(response, str):
        full_response = response
        console.print(
            Panel(
                Markdown(full_response),
                title="LLM",
                border_style=agent_response_style,
            )
        )
    else:
        with Live(console=console, refresh_per_second=REFRESH_RATE) as live:
            for chunk in response:
                full_response += chunk
                live.update(
                    Panel(
                        Markdown(full_response),
                        title="LLM",
                        border_style=agent_response_style,
                    )
                )
        console.print()  # Newline for separation
    return full_response


def display_stream_response(
    stream: Generator[AgentResponse, None, None] | str, console: Console
) -> str:
    """Display streaming response and return full response."""
    full_response = ""
    try:
        if isinstance(stream, str):
            full_response = display_response(stream, console)
        else:
            with Live(console=console, refresh_per_second=REFRESH_RATE) as live:
                for partial in stream:
                    display_actions(partial.actions, console)
                    display_thinking(getattr(partial, "thinking", ""), console)
                    if partial.response:
                        for chunk in partial.response:
                            full_response += chunk
                            live.update(
                                Panel(
                                    Markdown(full_response),
                                    title="LLM",
                                    border_style=agent_response_style,
                                )
                            )
            console.print()  # Newline for separation
    except Exception as e:
        from loguru import logger

        logger.error(f"Error during streaming: {e}")
        raise
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
        console.print(
            Panel(
                files_str,
                title="Files",
                style=context_style,
                border_style=context_style,
            )
        )


def get_user_input(
    session: PromptSession, context_manager: ContextManager
) -> str:
    """Prompt for and return user input."""
    from ..cli.theme import catppuccin_mocha_style

    prompt_text = f"{context_manager.current_mode.value} >> "
    return session.prompt(
        prompt_text,
        style=catppuccin_mocha_style,
    )
