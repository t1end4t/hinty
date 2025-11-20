import click
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import List

from ..baml_client.types import ConversationMessage
from ..cli.commands import help_command
from ..core.context_manager import ContextManager
from ..core.llm import get_agent_response

console = Console()


# Minimal LLM chat interface
def chat():
    session = PromptSession()
    style = Style.from_dict(
        {
            "prompt": "bold cyan",
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
                if user_input == "/help":
                    help_command(console)
                else:
                    console.print(f"Unknown command: {user_input}")
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
