import io
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Callable

from loguru import logger
from PIL import Image, ImageGrab
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console

from ..cli.theme import catppuccin_mocha_style
from ..core.project_manager import ProjectManager


def _get_clipboard_image() -> Image.Image | None:
    """Retrieve image from clipboard, supporting multiple platforms."""
    try:
        if sys.platform in ("win32", "darwin"):
            img = ImageGrab.grabclipboard()
            return img if isinstance(img, Image.Image) else None
        else:
            # Linux: Prefer Wayland (wl-paste)
            if shutil.which("wl-paste"):
                result = subprocess.run(
                    ["wl-paste", "--type", "image/png"],
                    capture_output=True,
                )
                if result.returncode == 0 and result.stdout:
                    return Image.open(io.BytesIO(result.stdout))

            # Fallback to X11 (xclip)
            if shutil.which("xclip"):
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
                    return Image.open(io.BytesIO(result.stdout))

            return None
    except Exception as e:
        logger.error(f"Failed to retrieve clipboard image: {e}")
        return None


def _create_prompt_continuation(
    prompt_text: str,
) -> Callable[[int, int, int], str]:
    """Generate continuation prompt for multiline input."""

    def continuation(width: int, line_number: int, wrap_count: int) -> str:
        if wrap_count > 0:
            return " " * len(prompt_text) + "-> "
        return prompt_text

    return continuation


def _handle_clipboard_paste(project_manager: ProjectManager) -> Callable:
    """Create handler for pasting images from clipboard."""

    def paste_handler(event):
        img = _get_clipboard_image()
        if img:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_filename = f"{timestamp}.png"
            img_path = project_manager.images_directory / img_filename
            img.save(img_path)
            project_manager.attach_file(img_path)
            logger.info(f"Image attached from clipboard: {img_path}")
        else:
            event.current_buffer.insert_text("[No image in clipboard]\n")

    return paste_handler


def _create_key_bindings(project_manager: ProjectManager) -> KeyBindings:
    """Set up custom key bindings for the prompt session."""
    bindings = KeyBindings()

    @bindings.add("enter")
    def _(event):
        event.current_buffer.validate_and_handle()

    @bindings.add("escape", "enter")  # Alt+Enter for newline
    def _(event):
        event.current_buffer.insert_text("\n")

    @bindings.add("c-v")  # Ctrl+V for clipboard paste
    def _(event):
        _handle_clipboard_paste(project_manager)(event)

    return bindings


def get_user_input(
    session: PromptSession, project_manager: ProjectManager, console: Console
) -> str:
    """Prompt for and return user input with custom bindings."""
    logger.info("Prompting for user input")
    prompt_text = f"{project_manager.mode.value} >> "
    continuation = _create_prompt_continuation(prompt_text)
    bindings = _create_key_bindings(project_manager)

    try:
        result = session.prompt(
            prompt_text,
            style=catppuccin_mocha_style,
            multiline=True,
            prompt_continuation=continuation,
            key_bindings=bindings,
        )
        logger.debug(f"User input received: {len(result)} characters")
        return result
    except Exception as e:
        logger.error(f"Error during user input prompt: {e}")
        raise
