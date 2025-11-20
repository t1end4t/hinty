import click
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.panel import Panel
from typing import List

from ..baml_client import b
from ..baml_client.types import ConversationMessage
from ..cli.commands import CommandCompleter, commands, handle_command
from ..cli.theme import catppuccin_mocha_style
from ..core.context_manager import ContextManager

console = Console()


# Minimal LLM chat interface
def chat():
    completer = CommandCompleter(commands)
    session = PromptSession(completer=completer, complete_while_typing=True)
    style = catppuccin_mocha_style

    console.print(
        Panel.fit(
            "Welcome to the Hinty CLI! Press Enter on an empty line to quit.",
            title="Hinty CLI",
            border_style="blue",
        )
    )

    conversation_history: List[ConversationMessage] = []
    context_manager = ContextManager()
    console.print(f"Current directory: {context_manager.pwd_path}")

    while True:
        try:
            user_input = session.prompt(">> ", style=style)
            if not user_input:
                break
            if user_input.startswith("/"):
                handle_command(user_input, console, conversation_history)
            else:
                user_message = ConversationMessage(
                    role="user", content=user_input
                )
                conversation_history.append(user_message)
                stream = b.stream.Router(user_input, conversation_history=conversation_history)
                previous = ""
                console.print("LLM:", style="green bold", end=" ")
                for partial in stream:
                    current = str(partial)
                    new_content = current[len(previous):]
                    if new_content:
                        console.print(new_content, end="", flush=True)
                    previous = current
                assistant_message = ConversationMessage(
                    role="assistant", content=previous
                )
                conversation_history.append(assistant_message)
                console.print()  # Newline after streaming
        except KeyboardInterrupt:
            break
        except EOFError:
            break


@click.command()
def create_cli():
    chat()
