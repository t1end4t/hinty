import os
from pathlib import Path
from typing import List

from prompt_toolkit.completion import Completer, Completion, PathCompleter
from prompt_toolkit.document import Document
from pyfzf import pyfzf
from rich.console import Console
from rich.panel import Panel

from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager
from ..core.models import Mode
from .theme import panel_border_style

commands = [
    "/help",
    "/clear",
    "/mode",
    "/add",
    "/files",
    "/drop",
    "/exit",
    "/quit",
]


class CommandCompleter(Completer):
    def __init__(self, commands, context_manager: ContextManager):
        self.commands = commands
        self.context_manager = context_manager
        self.path_completer = PathCompleter()

    def _get_add_completions(self, document, complete_event):
        text = document.text_before_cursor
        path_part = text[len("/add ") :]

        # Split by spaces to handle multiple files
        parts = path_part.split()
        if not parts:
            # No parts, complete from root
            last_part = ""
            start_offset = 0
        else:
            last_part = parts[-1]
            # Calculate start position for replacement: from the start of last_part
            start_offset = len(path_part) - len(last_part)

        path_document = Document(last_part, len(last_part))
        for completion in self.path_completer.get_completions(
            path_document, complete_event
        ):
            # Adjust start_position to replace only the last part
            yield Completion(
                completion.text,
                start_position=-len(last_part),
                display=completion.display,
            )

    def _get_drop_completions(self, text):
        if text == "/drop":
            # Complete with available file names
            for file_path in self.context_manager.get_all_files():
                yield Completion(
                    f" {file_path.name}",
                    start_position=0,
                    display=file_path.name,
                )
        elif text.startswith("/drop "):
            # Complete file names after "/drop "
            word = text[6:]  # Remove "/drop " prefix
            for file_path in self.context_manager.get_all_files():
                if file_path.name.startswith(word):
                    yield Completion(
                        file_path.name[len(word) :],
                        start_position=-len(word),
                        display=file_path.name,
                    )
        else:
            # Allow multiple file names, e.g., "/drop file1.txt file2.txt"
            pass  # No additional completions needed for now

    def _get_command_completions(self, text):
        word = text
        for command in self.commands:
            if command.startswith(word):
                yield Completion(
                    command,
                    start_position=-len(word),
                    display=command,
                )

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # If typing /add command, provide path completions
        if text.startswith("/add "):
            yield from self._get_add_completions(document, complete_event)

        # If typing /drop command, provide file name completions
        elif text.startswith("/drop"):
            yield from self._get_drop_completions(text)

        # Otherwise, provide command completions
        elif text.startswith("/"):
            yield from self._get_command_completions(text)


def help_command(console: Console) -> None:
    """Display help information for CLI commands."""
    help_text = (
        "Available commands:\n"
        "/help         - Show this help message\n"
        "/exit         - Exit the CLI\n"
        "/quit         - Quit the CLI\n"
        "/clear        - Clear conversation history and chat\n"
        "/files        - List current files in context\n"
        "/mode  <mode> - Change the current mode\n"
        "/add   <file> - Add file(s) to context (or interactive selection if no files)\n"
        "/drop  <file> - Drop file(s) from context by name, or all if no file\n"
        "Type a message to chat with Hinty. Use / to invoke commands."
    )
    panel = Panel(help_text, title="Help", border_style=panel_border_style)
    console.print(panel)


def clear_command(
    console: Console, conversation_history: List[ConversationMessage]
) -> None:
    """Clear conversation history and chat display."""
    conversation_history.clear()
    console.clear()
    console.print("Conversation history and chat cleared.\n")


def mode_command(
    command: str, console: Console, context_manager: ContextManager
) -> None:
    """Change the current mode."""
    parts = command.split()
    if len(parts) != 2:
        console.print("Usage: /mode <mode>\n")
        console.print(f"Available modes: {', '.join(Mode.get_values())}\n")
        return
    mode_str = parts[1]
    try:
        new_mode = Mode.from_string(mode_str)
        context_manager.set_mode(new_mode)
        console.print(f"Mode changed to {new_mode.value}\n")
    except ValueError:
        console.print(
            f"Invalid mode: {mode_str}. Available modes: {', '.join(Mode.get_values())}\n"
        )


def add_command(
    command: str, console: Console, context_manager: ContextManager
) -> None:
    """Add files to context for the agent/LLM."""
    parts = command.split()
    if len(parts) < 2:
        # Interactive mode: Fuzzy search and select files
        fzf = pyfzf.FzfPrompt()
        all_files = []
        for root, dirs, files in os.walk(context_manager.pwd_path):
            for file in files:
                all_files.append(
                    os.path.relpath(
                        os.path.join(root, file), context_manager.pwd_path
                    )
                )
        selected_files = fzf.prompt(
            all_files, "--multi"
        )  # Multi-select with fuzzy search
        if not selected_files:
            console.print("No files selected.\n")
            return
    else:
        # Direct mode: Use provided paths
        selected_files = parts[1:]

    # Validate and add files
    for file_path in selected_files:
        full_path = os.path.join(context_manager.pwd_path, file_path)
        if os.path.isfile(full_path):
            console.print(f"Added file: {file_path}\n")
            context_manager.add_file(Path(full_path))
        else:
            console.print(f"File not found: {file_path}\n")


def files_command(console: Console, context_manager: ContextManager) -> None:
    """List current files in context."""
    if not context_manager.get_all_files():
        console.print("No files attached.\n")
    else:
        console.print("Attached files:\n")
        for i, file_path in enumerate(context_manager.get_all_files()):
            console.print(f"  {i}: {file_path}\n")


def drop_command(
    command: str, console: Console, context_manager: ContextManager
) -> None:
    """Drop files from context by name, or all if no file provided."""
    parts = command.split()
    if len(parts) == 1:
        # No file provided: drop all files
        context_manager._files.clear()
        console.print("All files dropped from context.\n")
    else:
        # File names provided: drop specific files
        for file_name in parts[1:]:
            found = False
            for file_path in context_manager.get_all_files()[
                :
            ]:  # Copy to avoid modification during iteration
                if file_path.name == file_name:
                    context_manager.remove_file(file_path)
                    console.print(f"Dropped file: {file_path}\n")
                    found = True
                    break
            if not found:
                console.print(f"File not found: {file_name}\n")


def handle_command(
    command: str,
    console: Console,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
) -> None:
    """Dispatch commands to their handlers."""
    if command == "/help":
        help_command(console)
    elif command == "/clear":
        clear_command(console, conversation_history)
    elif command.startswith("/mode"):
        mode_command(command, console, context_manager)
    elif command.startswith("/add"):
        add_command(command, console, context_manager)
    elif command == "/files":
        files_command(console, context_manager)
    elif command.startswith("/drop"):
        drop_command(command, console, context_manager)
    elif command in ["/exit", "/quit"]:
        console.print("Exiting CLI...\n")
        raise SystemExit
    else:
        console.print(f"Unknown command: {command}\n")
