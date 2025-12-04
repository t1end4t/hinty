import re
from typing import List

import click
from baml_py import AbortController
from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style
from rich.console import Console

from ..baml_client.types import ConversationMessage
from ..cli.commands import CommandCompleter, commands, handle_command
from ..cli.utils import (
    display_files,
    display_stream_response,
    get_user_input,
    print_welcome,
)
from ..core.llm import get_agent_response
from ..core.project_manager import ProjectManager
from ..utils import cache_available_files

console = Console()


class BacktickLexer(Lexer):
    """Lexer to apply bold italic style to text between backticks."""

    def lex_document(self, document):
        def lex_line(line_no):
            line = document.lines[line_no]
            matches = list(re.finditer(r"`([^`]+)`", line))
            pos = 0
            result = []
            for match in matches:
                # Text before backtick
                if match.start() > pos:
                    result.append(("", line[pos : match.start()]))
                # Text inside backticks
                result.append(
                    ("bold italic", line[match.start() : match.end()])
                )
                pos = match.end()
            # Remaining text
            if pos < len(line):
                result.append(("", line[pos:]))
            return result

        return lex_line


def _setup_session(project_manager: ProjectManager) -> PromptSession:
    """Set up the prompt session with completer and style."""
    completer = CommandCompleter(commands, project_manager)

    style = Style.from_dict(
        {
            "bold italic": "bold italic",
            "default": "",
        }
    )

    session = PromptSession(
        completer=completer,
        complete_while_typing=True,
        history=FileHistory(str(project_manager.history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        lexer=BacktickLexer(),
        style=style,
    )
    return session


def _initialize_conversation() -> tuple[
    List[ConversationMessage], ProjectManager, AbortController
]:
    """Initialize conversation history and context manager."""
    conversation_history: List[ConversationMessage] = []
    project_manager = ProjectManager()
    controller = AbortController()

    console.print(f"Current directory: {project_manager.project_root}")

    # Cache available files synchronously
    cache_available_files(
        project_manager.project_root, project_manager.available_files_cache
    )

    return conversation_history, project_manager, controller


def _process_user_message(
    user_input: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
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
                project_manager,
                controller,
            )
            full_response = display_stream_response(responses, console)
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


def _process_input(
    console: Console,
    user_input: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
    controller: AbortController,
):
    """Process user input as a command or message."""
    if user_input.startswith("/"):
        handle_command(
            user_input, console, conversation_history, project_manager
        )
    else:
        _process_user_message(
            user_input,
            conversation_history,
            project_manager,
            console,
            controller,
        )


def _handle_input_loop(
    session: PromptSession,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
    controller: AbortController,
):
    """Handle the main input loop."""
    logger.debug("Starting input loop")
    while True:
        try:
            display_files(project_manager)
            user_input = get_user_input(session, project_manager)
            if not user_input:
                break

            _process_input(
                console,
                user_input,
                conversation_history,
                project_manager,
                controller,
            )

            logger.debug(f"Current mode: {project_manager.mode}")
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
def _chat():
    """Run the chat interface."""
    logger.debug("Starting chat")
    print_welcome()
    (
        conversation_history,
        project_manager,
        controller,
    ) = _initialize_conversation()
    session = _setup_session(project_manager)
    _handle_input_loop(
        session, conversation_history, project_manager, controller
    )
    logger.debug("Chat ended")


@click.command()
def create_cli():
    """Create and run the CLI."""
    _chat()
