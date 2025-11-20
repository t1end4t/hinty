import click
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import List

from ..baml_client.types import ConversationMessage
from ..cli.commands import CommandCompleter, commands, handle_command
from ..core.context_manager import ContextManager
from ..core.llm import get_agent_response

console = Console()


# Minimal LLM chat interface
def chat():
    completer = CommandCompleter(commands)
    session = PromptSession(completer=completer, complete_while_typing=True)
    style = Style.from_dict(
        {
            "prompt": "bold #89b4fa",  # Catppuccin Mocha Blue
            # Completion menu styles for Catppuccin Mocha theme
            "completion-menu": "bg:#1e1e2e #cdd6f4",  # Base bg, Text fg
            "completion-menu.completion": "bg:#313244 #cdd6f4",  # Surface0 bg, Text fg
            "completion-menu.completion.current": "bg:#45475a #f9e2af bold",  # Surface1 bg, Yellow fg, bold
            "completion-menu.meta": "bg:#1e1e2e #a6adc8",  # Base bg, Subtext0 fg
            "completion-menu.meta.current": "bg:#45475a #bac2de bold",  # Surface1 bg, Subtext1 fg, bold
        }
    )

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
                handle_command(user_input, console)
            else:
                user_message = ConversationMessage(
                    role="user", content=user_input
                )
                conversation_history.append(user_message)
                agent_response = get_agent_response(
                    user_input, conversation_history, context_manager
                )
                response = agent_response.response
                assistant_message = ConversationMessage(
                    role="assistant", content=response
                )
                conversation_history.append(assistant_message)
                console.print(
                    Panel.fit(
                        Text(response, style="green"),
                        title="LLM",
                        border_style="green",
                    )
                )
        except KeyboardInterrupt:
            break
        except EOFError:
            break


@click.command()
def create_cli():
    chat()
