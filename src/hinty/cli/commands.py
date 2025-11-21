import os
from pathlib import Path
from typing import List

from prompt_toolkit.completion import Completer, Completion, PathCompleter
from pyfzf import pyfzf
from rich.console import Console
from rich.panel import Panel

from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager
from ..core.models import Mode
from .theme import panel_border_style

commands = ["/help", "/clear", "/mode", "/add", "/exit", "/quit"]


class CommandCompleter(Completer):
    # def __init__(self, commands, context_manager: ContextManager):
    def __init__(self, commands):
        self.commands = commands
        # self.context_manager = context_manager
        self.path_completer = PathCompleter()

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # If typing /add command, provide path completions
        if text.startswith("/add "):
            # Extract the path part after "/add "
            path_part = text[5:]  # Remove "/add " prefix

            # Create a mock document for the path completer
            from prompt_toolkit.document import Document

            path_document = Document(path_part, len(path_part))

            # Get path completions and yield them
            for completion in self.path_completer.get_completions(
                path_document, complete_event
            ):
                yield completion

        # Otherwise, provide command completions
        elif text.startswith("/"):
            word = text
            for command in self.commands:
                if command.startswith(word):
                    yield Completion(
                        command,
                        start_position=-len(word),
                        display=command,
                    )


def help_command(console: Console) -> None:
    """Display help information for CLI commands."""
    help_text = (
        "Available commands:\n"
        "/help         - Show this help message\n"
        "/exit         - Exit the CLI\n"
        "/quit         - Quit the CLI\n"
        "/clear        - Clear conversation history and chat\n"
        "/mode  <mode> - Change the current mode\n"
        "/add   <file> - Add file(s) to context (or interactive selection if no files)\n"
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
    console.print("Conversation history and chat cleared.")


def mode_command(
    command: str, console: Console, context_manager: ContextManager
) -> None:
    """Change the current mode."""
    parts = command.split()
    if len(parts) != 2:
        console.print("Usage: /mode <mode>")
        console.print(f"Available modes: {', '.join(Mode.get_values())}")
        return
    mode_str = parts[1]
    try:
        new_mode = Mode.from_string(mode_str)
        context_manager.set_mode(new_mode)
        console.print(f"Mode changed to {new_mode.value}")
    except ValueError:
        console.print(
            f"Invalid mode: {mode_str}. Available modes: {', '.join(Mode.get_values())}"
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
            console.print("No files selected.")
            return
    else:
        # Direct mode: Use provided paths
        selected_files = parts[1:]

    # Validate and load files
    for file_path in selected_files:
        full_path = os.path.join(context_manager.pwd_path, file_path)
        if os.path.isfile(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                console.print(f"Added file: {file_path}")
                context_manager.add_file(Path(full_path))
            except Exception as e:
                console.print(f"Error reading {file_path}: {e}")
        else:
            console.print(f"File not found: {file_path}")


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
    elif command in ["/exit", "/quit"]:
        console.print("Exiting CLI...")
        raise SystemExit
    else:
        console.print(f"Unknown command: {command}")
