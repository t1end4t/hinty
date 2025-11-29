import asyncio
from typing import List

import click
from baml_py import AbortController
from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from rich.console import Console

from ..baml_client.types import ConversationMessage
from ..cli.commands import CommandCompleter, commands, handle_command
from ..cli.utils import (
    display_files,
    display_stream_response,
    get_user_input,
    print_welcome,
)
from ..core.context_manager import ContextManager
from ..core.llm import get_agent_response

console = Console()


def setup_session(context_manager: ContextManager) -> PromptSession:
    """Set up the prompt session with completer and style."""
    completer = CommandCompleter(commands, context_manager)

    session = PromptSession(
        completer=completer,
        complete_while_typing=True,
        history=FileHistory(str(context_manager.hinty_metadata / ".hinty_history")),
        auto_suggest=AutoSuggestFromHistory(),
    )
    return session


def initialize_conversation() -> tuple[
    List[ConversationMessage], ContextManager, AbortController
]:
    """Initialize conversation history and context manager."""
    conversation_history: List[ConversationMessage] = []
    context_manager = ContextManager()
    controller = AbortController()

    console.print(f"Current directory: {context_manager.pwd_path}")

    return conversation_history, context_manager, controller


async def process_user_message(
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

        with console.status("Thinking..."):
            responses = get_agent_response(
                user_input,
                conversation_history,
                context_manager,
                controller,
            )
            full_response = await display_stream_response(responses, console)
        assistant_message = ConversationMessage(
            role="assistant", content=full_response
        )
        conversation_history.append(assistant_message)
        logger.debug("User message processed")
    except KeyboardInterrupt:
        logger.warning("User interrupted LLM response")
        controller.abort()
        console.print("\n[yellow]Response interrupted.[/yellow]")
    except Exception as e:
        logger.error(f"Error processing user message: {e}")


async def process_input(
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
        await process_user_message(
            user_input,
            conversation_history,
            context_manager,
            console,
            controller,
        )


async def handle_input_loop(
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
            user_input = await get_user_input(session, context_manager)
            if not user_input:
                break
            await process_input(
                console,
                user_input,
                conversation_history,
                context_manager,
                controller,
            )

            logger.debug(f"Current mode: {context_manager.current_mode}")
        except KeyboardInterrupt:
            logger.info("Input loop interrupted by user")
            controller.abort()
            console.print(
                "\n[yellow]Interrupted. Type your next message or press Enter to quit.[/yellow]"
            )
            continue
        except EOFError:
            logger.info("Input loop ended due to EOF")
            controller.abort()
            break
        except Exception as e:
            logger.error(f"Unexpected error in input loop: {e}")
            console.print(f"[red]Error: {e}[/red]")
            controller.abort()
            continue
    logger.debug("Input loop ended")


# Minimal LLM chat interface
async def chat():
    """Run the chat interface."""
    logger.debug("Starting chat")
    print_welcome()
    conversation_history, context_manager, controller = (
        initialize_conversation()
    )
    session = setup_session(context_manager)
    await handle_input_loop(
        session, conversation_history, context_manager, controller
    )
    logger.debug("Chat ended")


@click.command()
def create_cli():
    """Create and run the CLI."""
    asyncio.run(chat())
