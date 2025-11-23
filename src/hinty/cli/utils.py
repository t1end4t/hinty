from typing import List

from baml_py import BamlSyncStream
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from prompt_toolkit import PromptSession

from ..baml_client.types import ConversationMessage
from ..cli.theme import llm_response_style, context_style
from ..core.context_manager import ContextManager

console = Console()

# Constants for readability
REFRESH_RATE = 4
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


def display_stream_response(
    stream: BamlSyncStream[str, str] | str, console: Console
) -> str:
    """Display streaming response and return full response."""
    full_response = ""
    try:
        if isinstance(stream, str):
            full_response = stream
            console.print(
                Panel(
                    Markdown(full_response),
                    title="LLM",
                    border_style=llm_response_style,
                )
            )
        else:
            with Live(console=console, refresh_per_second=REFRESH_RATE) as live:
                for partial in stream:
                    current = str(partial)
                    full_response = current
                    live.update(
                        Panel(
                            Markdown(full_response),
                            title="LLM",
                            border_style=llm_response_style,
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
