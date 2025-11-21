import os
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
        self.path_completer = PathCompleter(expanduser=True)

    def get_completions(self, document, complete_event):
        text = document.text
        if text.startswith("/"):
            if text.startswith("/mode "):
                prefix = "/mode "
                remaining = text[len(prefix) :]
                for mode in Mode.get_values():
                    if mode.startswith(remaining.lower()):
                        yield Completion(mode, start_position=-len(remaining))
            elif text.startswith("/add "):
                # Use PathCompleter for file paths after "/add "
                prefix = "/add "
                remaining = text[len(prefix) :]
                # Simulate a document for the path part
                from prompt_toolkit.document import Document

                path_doc = Document(remaining)
                for completion in self.path_completer.get_completions(
                    path_doc, complete_event
                ):
                    # Show full path by replacing from the start of remaining text
                    yield Completion(
                        completion.text,
                        start_position=-len(remaining),
                        display=completion.text,
                    )
            else:
                for cmd in self.commands:
                    if cmd.startswith(text.lower()):
                        yield Completion(cmd, start_position=-len(text))


def help_command(console: Console) -> None:
    """Display help information for CLI commands."""
    help_text = (
        "Available commands:\n"
        "/help        - Show this help message\n"
        "/clear       - Clear conversation history and chat\n"
        "/exit        - Exit the CLI\n"
        "/quit        - Quit the CLI\n"
        "/mode <mode> - Change the current mode\n"
        "/add <file>  - Add file(s) to context (or interactive selection if no files)\n"
        "Type a message to chat with the LLM. Use / to invoke commands."
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
