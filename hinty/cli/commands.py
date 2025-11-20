from rich.console import Console


def help_command(console: Console) -> None:
    """Display help information for CLI commands."""
    console.print(
        "Available commands:\n"
        "/help - Show this help message\n"
        "Type a message to chat with the LLM. Use / to invoke commands."
    )
