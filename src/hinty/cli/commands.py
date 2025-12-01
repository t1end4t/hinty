import os
from pathlib import Path
from typing import List

from prompt_toolkit.completion import (
    Completer,
    Completion,
    FuzzyCompleter,
    FuzzyWordCompleter,
    PathCompleter,
    CompleteEvent,
)
from prompt_toolkit.document import Document
from pyfzf import pyfzf
from rich.console import Console
from rich.panel import Panel

from ..baml_client.types import ConversationMessage
from ..core.project_manager import ProjectManager
from ..core.models import Mode
from .theme import YELLOW


commands = [
    "/add",
    "/clear",
    "/drop",
    "/exit",
    "/files",
    "/help",
    "/mode",
    "/quit",
]


class CommandCompleter(Completer):
    def __init__(self, commands, project_manager: ProjectManager):
        self.commands = commands
        self.project_manager = project_manager
        self.path_completer = FuzzyCompleter(PathCompleter())

    def _get_add_completions(
        self, document: Document, complete_event: CompleteEvent
    ):
        text = document.text_before_cursor
        path_part = text[len("/add ") :]

        all_files = []
        cache_path = self.project_manager.available_files_cache
        if cache_path.exists():
            with open(cache_path, "r") as f:
                all_files = [line.strip() for line in f if line.strip()]

        word_document = Document(path_part, len(path_part))
        completer = FuzzyWordCompleter(all_files)
        yield from completer.get_completions(word_document, complete_event)

    def _get_drop_completions(
        self, document: Document, complete_event: CompleteEvent
    ):
        text = document.text_before_cursor
        word = text[len("/drop ") :]
        names = [f.name for f in self.project_manager.get_attached_files()]
        word_document = Document(word, len(word))
        completer = FuzzyWordCompleter(names)
        yield from completer.get_completions(word_document, complete_event)

    def _get_mode_completions(
        self, document: Document, complete_event: CompleteEvent
    ):
        text = document.text_before_cursor
        word = text[len("/mode ") :]
        modes = Mode.get_values()
        word_document = Document(word, len(word))
        completer = FuzzyWordCompleter(modes)
        yield from completer.get_completions(word_document, complete_event)

    def _get_command_completions(self, text: str):
        word = text
        for command in self.commands:
            if command.startswith(word):
                yield Completion(
                    command,
                    start_position=-len(word),
                    display=command,
                )

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ):
        text = document.text_before_cursor

        # If typing /add command, provide path completions
        if text.startswith("/add "):
            yield from self._get_add_completions(document, complete_event)

        # If typing /drop command, provide file name completions
        elif text.startswith("/drop"):
            yield from self._get_drop_completions(document, complete_event)

        # If typing /mode command, provide mode completions
        elif text.startswith("/mode"):
            yield from self._get_mode_completions(document, complete_event)

        # Otherwise, provide command completions
        elif text.startswith("/"):
            yield from self._get_command_completions(text)


def help_command(console: Console):
    """Display help information for CLI commands."""
    help_text = (
        "Available commands:\n"
        "/clear        - Clear conversation history and chat\n"
        "/exit         - Exit the CLI\n"
        "/files        - List current files in context\n"
        "/help         - Show this help message\n"
        "/quit         - Quit the CLI\n"
        "/add   <file> - Add file to context (or interactive selection if no files)\n"
        "/drop  <file> - Drop file from context by name, or all if no file\n"
        "/mode  <mode> - Change the current mode\n"
        "Type a message to chat with Hinty. Use / to invoke commands."
    )
    panel = Panel(help_text, title="Help", border_style=YELLOW)
    console.print(panel, style=YELLOW)


def clear_command(
    console: Console, conversation_history: List[ConversationMessage]
):
    """Clear conversation history and chat display."""
    conversation_history.clear()
    console.clear()
    console.print("Conversation history and chat cleared.\n", style=YELLOW)


def mode_command(
    command: str, console: Console, project_manager: ProjectManager
):
    """Change the current mode."""
    parts = command.split()
    if len(parts) != 2:
        console.print("Usage: /mode <mode>\n", style=YELLOW)
        console.print(
            f"Available modes: {', '.join(Mode.get_values())}\n", style=YELLOW
        )
        return
    mode_str = parts[1]
    try:
        new_mode = Mode.from_string(mode_str)
        project_manager.change_mode(new_mode)
        console.print(f"Mode changed to {new_mode.value}\n", style=YELLOW)
    except ValueError:
        console.print(
            f"Invalid mode: {mode_str}. Available modes: {', '.join(Mode.get_values())}\n",
            style=YELLOW,
        )


def add_command(
    command: str, console: Console, project_manager: ProjectManager
):
    """Add files to context for the agent/LLM."""
    parts = command.split()
    if len(parts) < 2:
        # Interactive mode: Fuzzy search and select files
        fzf = pyfzf.FzfPrompt()
        all_files = []
        cache_path = project_manager.available_files_cache
        if cache_path.exists():
            with open(cache_path, "r") as f:
                all_files = [line.strip() for line in f if line.strip()]
        else:
            # Fallback to os.walk if cache doesn't exist
            for root, _, files in os.walk(project_manager.project_root):
                for file in files:
                    all_files.append(
                        os.path.relpath(
                            os.path.join(root, file),
                            project_manager.project_root,
                        )
                    )
        selected_files = fzf.prompt(
            all_files, "--multi"
        )  # Multi-select with fuzzy search
        if not selected_files:
            console.print("No files selected.\n", style=YELLOW)
            return
    else:
        # Direct mode: Use provided paths
        selected_files = parts[1:]

    # Validate and add files
    for file_path in selected_files:
        full_path = os.path.join(project_manager.project_root, file_path)
        if os.path.isfile(full_path):
            project_manager.attach_file(Path(full_path))
        else:
            console.print(f"File not found: {file_path}\n", style=YELLOW)


def files_command(console: Console, project_manager: ProjectManager):
    """List current files in context."""
    if not project_manager.get_attached_files():
        console.print("No files attached.\n", style=YELLOW)
    else:
        console.print("Attached files:\n", style=YELLOW)
        for i, file_path in enumerate(project_manager.get_attached_files()):
            console.print(f"  {i}: {file_path}\n", style=YELLOW)


def drop_command(
    command: str, console: Console, project_manager: ProjectManager
):
    """Drop files from context by name, or all if no file provided."""
    parts = command.split()
    if len(parts) == 1:
        project_manager.detach_file(remove_all=True)
        console.print("All files dropped from context.\n", style=YELLOW)
    else:
        # File names provided: drop specific files
        for file_name in parts[1:]:
            found = False
            for file_path in project_manager.get_attached_files()[
                :
            ]:  # Copy to avoid modification during iteration
                if file_path.name == file_name:
                    project_manager.detach_file(file_path)
                    console.print(f"Dropped file: {file_path}\n", style=YELLOW)
                    found = True
                    break
            if not found:
                console.print(f"File not found: {file_name}\n", style=YELLOW)


def handle_command(
    command: str,
    console: Console,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
):
    """Dispatch commands to their handlers."""
    if command == "/help":
        help_command(console)
    elif command == "/clear":
        clear_command(console, conversation_history)
    elif command.startswith("/mode"):
        mode_command(command, console, project_manager)
    elif command.startswith("/add"):
        add_command(command, console, project_manager)
    elif command == "/files":
        files_command(console, project_manager)
    elif command.startswith("/drop"):
        drop_command(command, console, project_manager)
    elif command in ["/exit", "/quit"]:
        console.print("Exiting CLI...\n", style=YELLOW)
        raise SystemExit
    else:
        console.print(f"Unknown command: {command}\n", style=YELLOW)
