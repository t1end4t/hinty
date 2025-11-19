import click
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import List

from ..baml_client.types import ConversationMessage
from ..core.context_manager import ContextManager
from ..core.llm import get_agent_response

console = Console()


# Minimal LLM chat interface - for now, just responds with "Hello" to any input
def chat():
    session = PromptSession()
    style = Style.from_dict(
        {
            "prompt": "bold cyan",
        }
    )

    console.print(
        Panel.fit(
            "Welcome to the LLM Chat CLI! Type 'exit' to quit.",
            title="Hinty CLI",
            border_style="blue",
        )
    )

    conversation_history: List[ConversationMessage] = []
    context_manager = ContextManager()

    while True:
        try:
            user_input = session.prompt("You: ", style=style)
            if user_input.lower() == "exit":
                break
            user_message = ConversationMessage(role="user", content=user_input)
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
