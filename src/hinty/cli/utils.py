import subprocess
from PIL import Image
import io
import shutil
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console

from ..cli.theme import catppuccin_mocha_style
from ..core.project_manager import ProjectManager
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


def _get_clipboard_image():
    """Get image from clipboard if available (supports both Wayland and X11)."""
    try:
        # Try Wayland first (wl-paste)
        if shutil.which("wl-paste"):
            result = subprocess.run(
                ["wl-paste", "--type", "image/png"],
                capture_output=True,
            )
            if result.returncode == 0 and result.stdout:
                img = Image.open(io.BytesIO(result.stdout))
                return img

        # Fallback to X11 (xclip)
        elif shutil.which("xclip"):
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
                capture_output=True,
            )
            if result.returncode == 0 and result.stdout:
                img = Image.open(io.BytesIO(result.stdout))
                return img

        return None
    except Exception as e:
        logger.error(f"Error getting clipboard image: {e}")
        return None


@bindings.add("c-v")  # Ctrl+V to paste image from clipboard
def _(event):
    img = _get_clipboard_image()
    if img:
        img.save("pasted_image.png")
        event.current_buffer.insert_text("[Image pasted: pasted_image.png]\n")
    else:
        event.current_buffer.insert_text("[No image in clipboard]\n")


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
