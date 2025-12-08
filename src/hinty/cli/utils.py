from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console

from ..cli.theme import catppuccin_mocha_style
from ..core.project_manager import ProjectManager
from .command_handlers import (
    add_command,
    clear_command,
    copy_command,
    drop_command,
    files_command,
    help_command,
    mode_command,
)
from .display_utils import display_files, display_stream_response, print_welcome
from loguru import logger

console = Console()

# Custom key bindings: Enter to accept, Alt+Enter to insert newline
bindings = KeyBindings()


@bindings.add("enter")
def _(event):
    event.current_buffer.validate_and_handle()


# Vt100 terminals translate the alt key into a leading escape key
@bindings.add("escape", "enter")
def _(event):
    event.current_buffer.insert_text("\n")


def get_user_input(
    session: PromptSession, project_manager: ProjectManager
) -> str:
    """Prompt for and return user input."""
    logger.info("Prompting for user input")
    prompt_text = f"{project_manager.mode.value} >> "

    def prompt_continuation(width, line_number, wrap_count):
        if wrap_count > 0:
            return " " * len(prompt_text) + "-> "
        else:
            return prompt_text

    try:
        result = session.prompt(
            prompt_text,
            style=catppuccin_mocha_style,
            multiline=True,
            prompt_continuation=prompt_continuation,
            key_bindings=bindings,
        )
        logger.debug(f"User input received: {len(result)} characters")
        return result
    except Exception as e:
        logger.error(f"Error getting user input: {e}")
        raise
