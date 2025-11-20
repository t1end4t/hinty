import click
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
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
                stream = b.stream.Router(
                    user_input, conversation_history=conversation_history
                )
                full_response = ""
                with Live(console=console, refresh_per_second=4) as live:
                    for partial in stream:
                        current = str(partial)
                        new_content = current[len(full_response) :]
                        full_response = current
                        # Render the current accumulated response as Markdown and update live
                        live.update(Markdown(full_response))

                # After streaming, add a newline for separation
                console.print()

                assistant_message = ConversationMessage(
                    role="assistant", content=full_response
                )

                conversation_history.append(assistant_message)
        except KeyboardInterrupt:
            break
        except EOFError:
            break


@click.command()
def create_cli():
    chat()
