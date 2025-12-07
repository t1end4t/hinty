import asyncio
import re
import threading
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


def _setup_session(project_manager: ProjectManager, conversation_history: List[ConversationMessage]) -> PromptSession:
    """Set up the prompt session with completer and style."""
    completer = CommandCompleter(commands, project_manager, conversation_history)

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

    cache_thread = threading.Thread(
        target=cache_available_files,
        args=(
            project_manager.project_root,
            project_manager.available_files_cache,
        ),
        daemon=True,
    )
    cache_thread.start()

    return conversation_history, project_manager, controller


async def _process_user_message(
    user_input: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
    console: Console,
    controller: AbortController,
):
    """Process a user message: append to history, stream response, update history."""
    user_message = ConversationMessage(role="user", content=user_input)
    conversation_history.append(user_message)
    try:
        with console.status("Thinking..."):
            responses = get_agent_response(
                user_input,
                conversation_history,
                project_manager,
                controller,
            )
            full_response = await display_stream_response(responses, console)
        assistant_message = ConversationMessage(
            role="assistant", content=full_response
        )
        conversation_history.append(assistant_message)
    except KeyboardInterrupt:
        logger.warning("User interrupted LLM response")
        controller.abort()
        console.print("\n[yellow]Response interrupted.[/yellow]")
    except Exception as e:
        logger.error(f"Error processing user message: {e}")


async def _process_input(
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
        await _process_user_message(
            user_input,
            conversation_history,
            project_manager,
            console,
            controller,
        )


async def _handle_input_loop(
    session: PromptSession,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
    controller: AbortController,
):
    """Handle the main input loop."""
    while True:
        try:
            display_files(project_manager)
            user_input = await asyncio.to_thread(
                get_user_input, session, project_manager
            )
            if not user_input:
                break

            await _process_input(
                console,
                user_input,
                conversation_history,
                project_manager,
                controller,
            )

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


# Minimal LLM chat interface
async def _chat():
    """Run the chat interface."""
    print_welcome()
    (
        conversation_history,
        project_manager,
        controller,
    ) = _initialize_conversation()
    session = _setup_session(project_manager, conversation_history)
    await _handle_input_loop(
        session, conversation_history, project_manager, controller
    )


@click.command()
def create_cli():
    """Create and run the CLI."""
    asyncio.run(_chat())
