import click
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from typing import List

from ..baml_client.types import ConversationMessage
from ..cli.commands import CommandCompleter, commands, handle_command
from ..cli.theme import catppuccin_mocha_style
from ..core.context_manager import ContextManager
from ..core.llm import get_agent_response

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
                        Markdown(response),
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
