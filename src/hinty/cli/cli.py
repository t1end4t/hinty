from typing import List

import click
from baml_py import AbortController, BamlSyncStream
from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from ..baml_client.types import ConversationMessage
from ..cli.commands import CommandCompleter, commands, handle_command
from ..cli.theme import (
    catppuccin_mocha_style,
    context_style,
    llm_response_style,
)
from ..core.context_manager import ContextManager
from ..core.llm import get_agent_response

console = Console()

# Constants for readability
REFRESH_RATE = 4
WELCOME_MESSAGE = (
    "Welcome to the Hinty CLI! Press Enter on an empty line to quit."
)


def setup_session(context_manager: ContextManager) -> PromptSession:
    """Set up the prompt session with completer and style."""
    completer = CommandCompleter(commands, context_manager)

    session = PromptSession(
        completer=completer,
        complete_while_typing=True,
        history=FileHistory(str(context_manager.pwd_path / ".hinty_history")),
        auto_suggest=AutoSuggestFromHistory(),
    )
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
    List[ConversationMessage], ContextManager, AbortController
]:
    """Initialize conversation history and context manager."""
    conversation_history: List[ConversationMessage] = []
    context_manager = ContextManager()
    controller = AbortController()

    console.print(f"Current directory: {context_manager.pwd_path}")

    return conversation_history, context_manager, controller


def display_stream_response(
    stream: BamlSyncStream[str, str] | str, console: Console
) -> str:
    """Display streaming response and return full response."""
    full_response = ""
    try:
        if isinstance(stream, str):
            full_response = stream
            console.print(
                Panel(
                    Markdown(full_response),
                    title="LLM",
                    style=llm_response_style,
                    border_style=llm_response_style,
                )
            )
        else:
            with Live(console=console, refresh_per_second=REFRESH_RATE) as live:
                for partial in stream:
                    current = str(partial)
                    full_response = current
                    live.update(
                        Panel(
                            Markdown(full_response),
                            title="LLM",
                            style=llm_response_style,
                            border_style=llm_response_style,
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
    context_manager: ContextManager,
    console: Console,
    controller: AbortController,
):
    """Process a user message: append to history, stream response, update history."""
    logger.debug("Processing user message")
    user_message = ConversationMessage(role="user", content=user_input)
    conversation_history.append(user_message)
    try:
        logger.debug("Calling external API for router")

        # NOTE: for now just show response
        stream = get_agent_response(
            user_input,
            conversation_history,
            context_manager,
            controller,
        )
        full_response = display_stream_response(stream.response, console)
        assistant_message = ConversationMessage(
            role="assistant", content=full_response
        )
        conversation_history.append(assistant_message)
        logger.debug("User message processed")
    except Exception as e:
        logger.error(f"Error processing user message: {e}")
        raise


def display_files(context_manager: ContextManager):
    """Display files panel if the file list is not empty."""
    files_str = (
        " ".join(
            str(f.relative_to(context_manager.pwd_path))
            for f in context_manager.get_all_files()
        )
        if context_manager.get_all_files()
        else ""
    )
    if files_str:
        console.print(
            Panel(
                files_str,
                title="Files",
                style=context_style,
                border_style=context_style,
            )
        )


def get_user_input(
    session: PromptSession, context_manager: ContextManager
) -> str:
    """Prompt for and return user input."""
    prompt_text = f"{context_manager.current_mode.value} >> "
    return session.prompt(
        prompt_text,
        style=catppuccin_mocha_style,
    )


def process_input(
    console: Console,
    user_input: str,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
    controller: AbortController,
):
    """Process user input as a command or message."""
    if user_input.startswith("/"):
        handle_command(
            user_input, console, conversation_history, context_manager
        )
    else:
        process_user_message(
            user_input,
            conversation_history,
            context_manager,
            console,
            controller,
        )


def handle_input_loop(
    session: PromptSession,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
    controller: AbortController,
):
    """Handle the main input loop."""
    logger.debug("Starting input loop")
    while True:
        try:
            display_files(context_manager)
            user_input = get_user_input(session, context_manager)
            if not user_input:
                break
            process_input(
                console,
                user_input,
                conversation_history,
                context_manager,
                controller,
            )

            logger.debug(f"Current mode: {context_manager.current_mode}")
        except KeyboardInterrupt:
            logger.info(
                "Input loop interrupted by user (first time), aborting request"
            )
            controller.abort()  # Abort any ongoing request
        except EOFError:
            logger.info("Input loop ended due to EOF")
            controller.abort()  # Abort any ongoing request
            break
        except Exception as e:
            logger.error(f"Unexpected error in input loop: {e}")
            break
    logger.debug("Input loop ended")


# Minimal LLM chat interface
def chat():
    """Run the chat interface."""
    logger.debug("Starting chat")
    print_welcome()
    conversation_history, context_manager, controller = (
        initialize_conversation()
    )
    session = setup_session(context_manager)
    handle_input_loop(
        session, conversation_history, context_manager, controller
    )
    logger.debug("Chat ended")


@click.command()
def create_cli():
    """Create and run the CLI."""
    logger.debug("Creating CLI")
    chat()
    logger.debug("CLI created")
