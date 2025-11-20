import click
import time
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
                handle_command(user_input, console, conversation_history)
            else:
                user_message = ConversationMessage(
                    role="user", content=user_input
                )
                conversation_history.append(user_message)
                agent_response = get_agent_response(
                    user_input, conversation_history, context_manager
                )
                response = agent_response.response
                # Handle streaming or string response
                if hasattr(response, '__iter__') and not isinstance(response, str):
                    # Assume it's a stream like BamlSyncStream
                    console.print("LLM:", style="green bold", end=" ")
                    previous = ""
                    full_response = ""
                    for partial in response:
                        current = str(partial)
                        new_content = current[len(previous):]
                        if new_content:
                            console.print(new_content, end="", style="green", flush=True)
                        full_response += new_content
                        previous = current
                    console.print()  # Newline after streaming
                    response_content = full_response
                else:
                    # Fallback for string response
                    response_content = str(response)
                    words = response_content.split()
                    console.print("LLM:", style="green bold", end=" ")
                    for word in words:
                        console.print(word, end=" ", style="green")
                        time.sleep(0.05)
                    console.print()
                assistant_message = ConversationMessage(
                    role="assistant", content=response_content
                )
                conversation_history.append(assistant_message)
        except KeyboardInterrupt:
            break
        except EOFError:
            break


@click.command()
def create_cli():
    chat()
