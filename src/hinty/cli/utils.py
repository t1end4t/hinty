from typing import Generator

from baml_py import BamlSyncStream
from prompt_toolkit import PromptSession
from rich.console import Console
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


def display_actions(actions: list[str], console: Console):
    """Display actions with a specific theme."""
    if actions:
        console.print(f"[bold {agent_action_style}]{', '.join(actions)}[/]")


def display_thinking(thinking: str, console: Console):
    """Display thinking with a specific theme."""
    if thinking:
        console.print(f"[bold {agent_thinking_style}]Thinking:[/]")
        console.print(Markdown(thinking))


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


def display_stream_response(
    stream: Generator[AgentResponse, None, None], console: Console
) -> str:
    """Display streaming response and return full response."""
    full_response = ""
    cumulative_content = ""
    try:
        with Live(console=console, refresh_per_second=REFRESH_RATE) as live:
            for partial in stream:
                # Accumulate thinking
                if partial.thinking:
                    cumulative_content += (
                        f"**Thinking:**\n{partial.thinking}\n\n"
                    )

                # Accumulate actions
                if partial.actions:
                    cumulative_content += (
                        f"**Actions:** {', '.join(partial.actions)}\n\n"
                    )

                # Accumulate and show response
                if partial.response:
                    if isinstance(partial.response, str):
                        full_response = partial.response
                        cumulative_content += (
                            f"**Response:**\n{full_response}\n"
                        )
                        live.update(
                            Panel(
                                Markdown(cumulative_content),
                                title="LLM",
                                border_style=agent_response_style,
                            )
                        )
                    else:
                        cumulative_content += "**Response:**\n"
                        for chunk in partial.response:
                            full_response = chunk
                            # Update the last line with the chunk
                            lines = cumulative_content.split("\n")
                            lines[-1] = full_response
                            cumulative_content = "\n".join(lines)
                            live.update(
                                Panel(
                                    Markdown(cumulative_content),
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
        console.print(f"[{context_style}]Files: {files_str}[/]")


def get_user_input(
    session: PromptSession, context_manager: ContextManager
) -> str:
    """Prompt for and return user input."""

    prompt_text = f"{context_manager.current_mode.value} >> "
    return session.prompt(
        prompt_text,
        style=catppuccin_mocha_style,
    )
