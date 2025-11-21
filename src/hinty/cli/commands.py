from typing import List

from prompt_toolkit.completion import Completer, Completion
from rich.console import Console

from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager
from ..core.models import Mode

commands = ["/help", "/clear", "/mode"]


class CommandCompleter(Completer):
    def __init__(self, commands):
        self.commands = commands

    def get_completions(self, document, complete_event):
        text = document.text
        if text.startswith("/"):
            for cmd in self.commands:
                if cmd.startswith(text.lower()):
                    yield Completion(cmd, start_position=-len(text))


def help_command(console: Console) -> None:
    """Display help information for CLI commands."""
    console.print(
        "Available commands:\n"
        "/help - Show this help message\n"
        "/clear - Clear conversation history and chat\n"
        "/mode <mode> - Change the current mode\n"
        "Type a message to chat with the LLM. Use / to invoke commands."
    )


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
        context_manager.current_mode = new_mode
        console.print(f"Mode changed to {new_mode.value}")
    except ValueError:
        console.print(
            f"Invalid mode: {mode_str}. Available modes: {', '.join(Mode.get_values())}"
        )


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
    else:
        console.print(f"Unknown command: {command}")
