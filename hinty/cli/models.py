from enum import Enum
from pathlib import Path
from typing import Callable, Iterator, List

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from pydantic import BaseModel
from rich.console import Console

from .context_manager import ProjectContext
from .theme import BaseTheme


class Mode(Enum):
    ROUTER = "smart"  # later

    @classmethod
    def from_string(cls, value: str) -> "Mode":
        """Convert string to Mode enum."""
        for mode in cls:
            if mode.value == value.lower():
                return mode
        raise ValueError(f"Unknown mode: {value}")

    @classmethod
    def get_values(cls) -> List[str]:
        """Get all mode values as strings."""
        return [mode.value for mode in cls]


class Command(BaseModel):
    """Represents a slash command with its name and description."""

    name: str
    description: str


# Define commands list for reuse
COMMANDS: List[Command] = [
    Command(name="/add", description="Add context to conversation"),
    Command(name="/exit", description="Exit chat session"),
    Command(name="/quit", description="Exit chat session"),
    Command(name="/help", description="Show help information"),
    Command(name="/mode", description="Change conversation mode"),
    Command(name="/init", description="Initialize new project"),
]


class SlashCommandCompleter(Completer):
    """Completer for slash commands."""

    def __init__(self):
        self.commands: List[Command] = COMMANDS

    def get_completions(
        self, document: Document, complete_event: object
    ) -> Iterator[Completion]:
        text = document.text_before_cursor.lstrip()
        if not text.startswith("/"):
            return

        if text.startswith("/mode "):
            yield from self._get_mode_completions(text)
        elif text.startswith("/add "):
            yield from self._get_file_completions(text)
        else:
            yield from self._get_command_completions(text)

    def _get_mode_completions(self, text: str) -> Iterator[Completion]:
        """Get completions for mode selection."""
        mode_text = text[6:]  # After "/mode "
        for option in Mode.get_values():
            if option.startswith(mode_text):
                yield Completion(option, start_position=-len(mode_text))

    def _get_command_completions(self, text: str) -> Iterator[Completion]:
        """Get completions for slash commands."""
        for command in self.commands:
            if command.name.startswith(text):
                yield Completion(command.name, start_position=-len(text))

    def _get_file_completions(self, text: str) -> Iterator[Completion]:
        """Get file and directory completions for the /add command."""
        path_text = text[5:]  # After "/add "

        try:
            # Determine the directory to search in
            if "/" in path_text:
                # User is typing a path, get the directory part
                dir_part = "/".join(path_text.split("/")[:-1])
                file_part = path_text.split("/")[-1]
                search_dir = Path(dir_part) if dir_part else Path(".")
            else:
                # User is typing in current directory
                search_dir = Path(".")
                file_part = path_text

            # Show files and directories in the current search directory
            if search_dir.exists() and search_dir.is_dir():
                # If path_text ends with "/" and points to a directory, show its contents
                if (
                    path_text.endswith("/")
                    and (search_dir / path_text.rstrip("/")).is_dir()
                ):
                    target_dir = search_dir / path_text.rstrip("/")
                    for item in target_dir.iterdir():
                        if item.name.startswith("."):
                            continue  # Skip hidden files/directories

                        full_path = path_text + item.name
                        if item.is_dir():
                            yield Completion(
                                full_path + "/",
                                start_position=-len(path_text),
                                display_meta="directory",
                            )
                        else:
                            yield Completion(
                                full_path,
                                start_position=-len(path_text),
                                display_meta="file",
                            )
                else:
                    # Normal completion for current directory
                    for item in search_dir.iterdir():
                        if item.name.startswith("."):
                            continue  # Skip hidden files/directories

                        item_name = item.name
                        if "/" in path_text:
                            # Include the directory path
                            full_path = str(search_dir / item_name)
                        else:
                            full_path = item_name

                        if item_name.startswith(file_part):
                            if item.is_dir():
                                yield Completion(
                                    full_path + "/",
                                    start_position=-len(path_text),
                                    display_meta="directory",
                                )
                            else:
                                yield Completion(
                                    full_path,
                                    start_position=-len(path_text),
                                    display_meta="file",
                                )
        except PermissionError:
            pass  # Skip directories we can't access


# Type definitions
CommandHandler = Callable[[Console, BaseTheme, ProjectContext], bool]
ModeCommandHandler = Callable[[str, Console, BaseTheme, Mode], Mode]
