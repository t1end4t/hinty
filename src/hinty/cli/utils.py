import io
import shutil
import subprocess
import sys
from datetime import datetime

from loguru import logger
from PIL import Image, ImageGrab
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console

from ..cli.theme import catppuccin_mocha_style
from ..core.project_manager import ProjectManager
from ..cli.display_utils import display_files


def _get_clipboard_image():
    """Get image from clipboard if available (cross-platform support)."""
    try:
        if sys.platform in ("win32", "darwin"):
            # Use PIL's ImageGrab for Windows and macOS
            img = ImageGrab.grabclipboard()
            return img if isinstance(img, Image.Image) else None
        else:
            # Linux: Try Wayland first (wl-paste)
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
                    [
                        "xclip",
                        "-selection",
                        "clipboard",
                        "-t",
                        "image/png",
                        "-o",
                    ],
                    capture_output=True,
                )
                if result.returncode == 0 and result.stdout:
                    img = Image.open(io.BytesIO(result.stdout))
                    return img

            return None
    except Exception as e:
        logger.error(f"Error getting clipboard image: {e}")
        return None


def get_user_input(
    session: PromptSession, project_manager: ProjectManager, console: Console
) -> str:
    """Prompt for and return user input."""
    logger.info("Prompting for user input")
    prompt_text = f"{project_manager.mode.value} >> "

    def prompt_continuation(width, line_number, wrap_count):
        if wrap_count > 0:
            return " " * len(prompt_text) + "-> "
        else:
            return prompt_text

    # Custom key bindings: Enter to accept, Alt+Enter to insert newline
    bindings = KeyBindings()

    @bindings.add("enter")
    def _(event):
        event.current_buffer.validate_and_handle()

    # Vt100 terminals translate the alt key into a leading escape key
    @bindings.add("escape", "enter")
    def _(event):
        event.current_buffer.insert_text("\n")

    @bindings.add("c-v")  # Ctrl+V to paste image from clipboard
    def _(event):
        img = _get_clipboard_image()
        if img:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_filename = f"{timestamp}.png"
            img_path = project_manager.images_directory / img_filename
            img.save(img_path)
            project_manager.attach_file(img_path)
        else:
            event.current_buffer.insert_text("[No image in clipboard]\n")

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
