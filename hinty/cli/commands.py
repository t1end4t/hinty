from prompt_toolkit.completion import Completer, Completion
from rich.console import Console


commands = ["/help"]


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
        "Type a message to chat with the LLM. Use / to invoke commands."
    )


def handle_command(command: str, console: Console) -> None:
    """Dispatch commands to their handlers."""
    if command == "/help":
        help_command(console)
    else:
        console.print(f"Unknown command: {command}")
