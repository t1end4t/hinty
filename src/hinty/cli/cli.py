import click
from loguru import logger
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from typing import List

from ..baml_client import b
from ..baml_client.types import ConversationMessage
from ..cli.commands import CommandCompleter, commands, handle_command
from ..cli.theme import catppuccin_mocha_style, panel_border_style
from ..core.context_manager import ContextManager

console = Console()

# Constants for readability
WELCOME_MESSAGE = (
    "Welcome to the Hinty CLI! Press Enter on an empty line to quit."
)
PROMPT_TEXT = ">> "
REFRESH_RATE = 4


def setup_session() -> PromptSession:
    """Set up the prompt session with completer and style."""
    completer = CommandCompleter(commands)
    session = PromptSession(completer=completer, complete_while_typing=True)
    return session


def print_welcome():
    """Print the welcome panel."""
    console.print(
        Panel.fit(
            WELCOME_MESSAGE,
            title="Hinty CLI",
            border_style="blue",
        )
    )


def initialize_conversation() -> tuple[
    List[ConversationMessage], ContextManager
]:
    """Initialize conversation history and context manager."""
    conversation_history: List[ConversationMessage] = []
    context_manager = ContextManager()
    console.print(f"Current directory: {context_manager.pwd_path}")
    return conversation_history, context_manager


def display_stream_response(stream, console: Console) -> str:
    """Display streaming response and return full response."""
    full_response = ""
    try:
        with Live(console=console, refresh_per_second=REFRESH_RATE) as live:
            for partial in stream:
                current = str(partial)
                full_response = current
                live.update(
                    Panel(
                        Markdown(full_response),
                        title="LLM",
                        border_style=panel_border_style,
                    )
                )
        console.print()  # Newline for separation
    except Exception as e:
        logger.error(f"Error during streaming: {e}")
        raise
    return full_response


def process_user_message(
    user_input: str,
    conversation_history: List[ConversationMessage],
    console: Console,
) -> None:
    """Process a user message: append to history, stream response, update history."""
    logger.debug("Processing user message")
    user_message = ConversationMessage(role="user", content=user_input)
    conversation_history.append(user_message)
    try:
        logger.debug("Calling external API for router")
        stream = b.stream.Router(
            user_input, conversation_history=conversation_history
        )
        full_response = display_stream_response(stream, console)
        assistant_message = ConversationMessage(
            role="assistant", content=full_response
        )
        conversation_history.append(assistant_message)
        logger.debug("User message processed")
    except Exception as e:
        logger.error(f"Error processing user message: {e}")
        raise


def handle_input_loop(
    session: PromptSession,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
) -> None:
    """Handle the main input loop."""
    logger.debug("Starting input loop")
    style = catppuccin_mocha_style
    last_files = None
    while True:
        try:
            files_str = (
                " ".join(
                    str(f.relative_to(context_manager.pwd_path))
                    for f in context_manager._files
                )
                if context_manager._files
                else ""
            )
            if files_str != last_files:
                if files_str:
                    console.print(f"Added {files_str} to the chat")
                    console.print(
                        "───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────"
                    )
                    console.print("Readonly: CLAUDE.md")
                    console.print(f"Editable: {files_str}")
                last_files = files_str
            prompt_text = f"{context_manager.current_mode.value} >> "
            user_input = session.prompt(prompt_text, style=style)
            if not user_input:
                break
            if user_input.startswith("/"):
                handle_command(
                    user_input, console, conversation_history, context_manager
                )
            else:
                process_user_message(user_input, conversation_history, console)
        except KeyboardInterrupt:
            break
        except EOFError:
            break
        except Exception as e:
            logger.error(f"Unexpected error in input loop: {e}")
            break
    logger.debug("Input loop ended")


# Minimal LLM chat interface
def chat():
    """Run the chat interface."""
    logger.debug("Starting chat")
    session = setup_session()
    print_welcome()
    conversation_history, context_manager = initialize_conversation()
    handle_input_loop(session, conversation_history, context_manager)
    logger.debug("Chat ended")


@click.command()
def create_cli():
    """Create and run the CLI."""
    logger.debug("Creating CLI")
    chat()
    logger.debug("CLI created")
