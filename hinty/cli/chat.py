from typing import Any, List

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..baml_client.types import ConversationMessage
from .commands import Mode, handle_slash_command
from .context_manager import ProjectContext
from .llm import get_agent_response
from .models import SlashCommandCompleter
from .theme import BaseTheme, create_catppuccin_theme, create_style


def print_welcome_message(console: Console, theme: BaseTheme):
    """Print welcome message."""
    console.print(
        f"[bold {theme.blue}]Hinty not make you dumb![/bold {theme.blue}]"
    )
    console.print(
        f"[{theme.overlay0}]Type '/exit' or '/quit' to quit the chat.[/{theme.overlay0}]"
    )
    console.print(
        f"[{theme.overlay0}]Use '/add' to add context.[/{theme.overlay0}]\n"
    )


def display_response(response: str, console: Console, theme: BaseTheme):
    """Display LLM response with formatting."""
    console.print(
        Panel(
            Markdown(response),
            title=f"[bold {theme.green}]Agent Response[/bold {theme.green}]",
            border_style=theme.green,
        )
    )


def handle_keyboard_interrupt(console: Console, theme: BaseTheme):
    """Handle keyboard interrupt."""
    console.print(f"\n[bold {theme.yellow}]Goodbye![/bold {theme.yellow}]")


def process_user_input(
    user_input: str,
    console: Console,
    theme: BaseTheme,
    conversation_history: List[ConversationMessage],
    current_mode: Mode,
    project_manager: ProjectContext,
) -> tuple[bool, Mode]:
    """Process user input and return (should_exit, new_mode)."""
    if user_input.startswith("/"):
        return handle_slash_command(
            user_input, console, theme, current_mode, project_manager
        )

    if user_input.strip() == "":
        return False, current_mode

    # Add user message to conversation history
    conversation_history.append(
        ConversationMessage(role="user", content=user_input)
    )

    # Get response from LLM with loading animation
    if current_mode == Mode.ROUTER:
        # For other modes, use spinner
        with console.status(
            f"[{theme.blue}]Thinking...",
            spinner="dots",
            spinner_style=theme.blue,
        ):
            response = get_agent_response(
                user_input, conversation_history, current_mode, project_manager
            )

    # Add assistant response to conversation history
    conversation_history.append(
        ConversationMessage(role="assistant", content=response)
    )

    display_response(response, console, theme)
    return False, current_mode


def display_context_info(
    theme: BaseTheme,
    context_manager: ProjectContext,
):
    """Display context information including files and paths."""
    content_lines = []

    # Display context files
    if context_manager.has_files():
        files = context_manager.get_files()
        file_list = " ".join(
            [f"[{theme.green}]{file.name}[/{theme.green}]" for file in files]
        )
        content_lines.append(file_list)


def start_chat():
    """Start a chat session with the LLM."""
    console = Console()
    theme = create_catppuccin_theme()
    style = create_style(theme)
    conversation_history: List[ConversationMessage] = []

    current_mode = Mode.ROUTER
    context_manager = ProjectContext()

    # Print current working directory at start
    pwd_path = context_manager.get_pwd_path()
    if pwd_path:
        console.print(f"[{theme.blue}](pwd):[/{theme.blue}] {pwd_path}")

    print_welcome_message(console, theme)

    session: PromptSession[Any] = PromptSession(
        completer=SlashCommandCompleter(), style=style
    )

    while True:
        try:
            # Display context information before prompt
            display_context_info(theme, context_manager)

            prompt_text = FormattedText(
                [
                    (f"bold {theme.blue}", f"[{current_mode.value}]"),
                    ("", " "),
                    (theme.green, ">>"),
                    ("", " "),
                ]
            )
            user_input: str = session.prompt(prompt_text)
            should_exit, current_mode = process_user_input(
                user_input,
                console,
                theme,
                conversation_history,
                current_mode,
                context_manager,
            )
            if should_exit:
                break

        except KeyboardInterrupt:
            handle_keyboard_interrupt(console, theme)
            break
        except EOFError:
            handle_keyboard_interrupt(console, theme)
            break
