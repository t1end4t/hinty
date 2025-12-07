import os
import re
import threading
from pathlib import Path
from typing import AsyncGenerator, List

import pyperclip
from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import choice
from pyfzf import pyfzf
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from ..baml_client.types import ConversationMessage
from ..cli.theme import (
    agent_action_style,
    agent_response_style,
    agent_thinking_style,
    catppuccin_mocha_style,
    context_style,
)
from ..core.models import AgentResponse, Mode
from ..core.project_manager import ProjectManager
from ..utils.cache import cache_objects
from .theme import YELLOW

console = Console()

# Constants for readability
REFRESH_RATE = 100
WELCOME_MESSAGE = (
    "Welcome to the Hinty CLI! Press Enter on an empty line to quit."
)


def print_welcome():
    """Print the welcome panel."""
    console.print(
        Panel.fit(
            WELCOME_MESSAGE,
            title="Hinty CLI",
            border_style="blue",
        )
    )


async def display_stream_response(
    stream: AsyncGenerator[AgentResponse, None], console: Console
) -> str:
    """Display streaming response and return full response."""
    logger.info("Starting to display stream response")
    current_response = ""
    current_actions = []
    current_thinking = None
    full_response = ""
    console_height = console.height

    live = Live(
        console=console, refresh_per_second=REFRESH_RATE, transient=True
    )
    live.start()
    try:
        async for partial in stream:
            # show thinking
            if partial.thinking:
                current_thinking = partial.thinking

            # show actions
            if partial.actions:
                current_actions = partial.actions

            # accumulate and show response
            if partial.response:
                if isinstance(partial.response, str):
                    current_response = partial.response
                    full_response = current_response
                else:
                    # Handle stream case by consuming chunks
                    for chunk in partial.response:
                        full_response = chunk
                        # Split into lines and take only the last N lines
                        lines = chunk.split("\n")
                        last_lines = lines[-console_height:]
                        current_response = "\n".join(last_lines)

                # Update live display with truncated response
                group_items = []
                if current_thinking:
                    group_items.append(
                        Group(
                            f"[bold {agent_thinking_style}]Thinking:[/]",
                            Markdown(current_thinking),
                        )
                    )
                group_items.append(
                    Panel(
                        Markdown(current_response),
                        title="LLM",
                        border_style=agent_response_style,
                    )
                )
                if current_actions:
                    group_items.append(
                        f"[bold {agent_action_style}]{', '.join(current_actions)}[/]"
                    )
                live.update(Group(*group_items))
            else:
                # No response, but update for actions
                group_items = []
                if current_thinking:
                    group_items.append(
                        Group(
                            f"[bold {agent_thinking_style}]Thinking:[/]",
                            Markdown(current_thinking),
                        )
                    )
                if current_response:
                    group_items.append(
                        Panel(
                            Markdown(current_response),
                            title="LLM",
                            border_style=agent_response_style,
                        )
                    )
                if current_actions:
                    group_items.append(
                        f"[bold {agent_action_style}]{', '.join(current_actions)}[/]"
                    )
                live.update(Group(*group_items))
    except Exception as e:
        logger.error(f"Error during stream response display: {e}")
        raise
    finally:
        # Clear the live display before stopping
        live.update("")
        live.stop()

    # Print final response normally (cursor stays at bottom)
    if full_response:
        group_items = []
        if current_thinking:
            group_items.append(
                Group(
                    f"[bold {agent_thinking_style}]Thinking:[/]",
                    Markdown(current_thinking),
                )
            )
        if current_actions:
            group_items.append(
                f"[bold {agent_action_style}]{', '.join(current_actions)}[/]"
            )

        # NOTE: in final response, show thinking and action before response
        group_items.append(
            Panel(
                Markdown(full_response),
                title="LLM",
                border_style=agent_response_style,
            )
        )
        console.print(Group(*group_items))
        # add new line
        console.print()

    logger.info("Finished displaying stream response")
    return full_response


def display_files(project_manager: ProjectManager):
    """Display files panel if the file list is not empty."""
    files_str = (
        " ".join(
            str(f.relative_to(project_manager.project_root))
            for f in project_manager.get_attached_files()
        )
        if project_manager.get_attached_files()
        else ""
    )
    if files_str:
        console.print(f"[{context_style}]Files: {files_str}[/]")


def get_user_input(
    session: PromptSession, project_manager: ProjectManager
) -> str:
    """Prompt for and return user input."""
    logger.info("Prompting for user input")
    prompt_text = f"{project_manager.mode.value} >> "
    try:
        result = session.prompt(
            prompt_text,
            style=catppuccin_mocha_style,
        )
        logger.debug(f"User input received: {len(result)} characters")
        return result
    except Exception as e:
        logger.error(f"Error getting user input: {e}")
        raise


def help_command(console: Console):
    """Display help information for CLI commands."""
    help_text = (
        "Available commands:\n"
        "/clear                     - Clear conversation history and chat\n"
        "/exit                      - Exit the CLI\n"
        "/files                     - List current files in context\n"
        "/help                      - Show this help message\n"
        "/quit                      - Quit the CLI\n"
        "/add   <file>              - Add file to context (or interactive selection if no files)\n"
        "/drop  <file>              - Drop file from context by name, or all if no file\n"
        "/mode  <mode>              - Change the current mode\n"
        "/copy  <full|code `index`> - Copy last response or code blocks\n"
        "Type a message to chat with Hinty. Use / to invoke commands."
    )
    panel = Panel(help_text, title="Help", border_style=YELLOW)
    console.print(panel, style=YELLOW)


def clear_command(
    console: Console, conversation_history: List[ConversationMessage]
):
    """Clear conversation history and chat display."""
    conversation_history.clear()
    console.clear()
    console.print("Conversation history and chat cleared.\n", style=YELLOW)


def copy_command(
    command: str,
    console: Console,
    conversation_history: List[ConversationMessage],
):
    """Copy the last LLM response or parts of it to clipboard."""
    # Find the last assistant message
    last_msg = None
    for msg in reversed(conversation_history):
        if msg.role == "assistant":
            last_msg = msg
            break
    if not last_msg:
        console.print("No LLM response found.\n", style=YELLOW)
        return
    
    code_blocks = re.findall(
        r"```[\w]*\n(.*?)\n```", last_msg.content, re.DOTALL
    )
    if code_blocks:
        # Offer choice between full and code
        options = [
            ("full", "Full response"),
            ("code", "Code blocks"),
        ]
        try:
            selected_type = choice(
                message="What to copy?",
                options=options,
            )
        except KeyboardInterrupt:
            console.print("Copy cancelled.\n", style=YELLOW)
            return
        if selected_type == "full":
            content_to_copy = last_msg.content
        elif selected_type == "code":
            # Choose which block
            block_options = [
                (i, f"Block {i + 1}: {block.splitlines()[0][:50]}...")
                for i, block in enumerate(code_blocks)
            ]
            if len(block_options) == 1:
                selected_index = 0
            else:
                try:
                    selected_index = choice(
                        message="Choose a code block to copy:",
                        options=block_options,
                    )
                except KeyboardInterrupt:
                    console.print("Copy cancelled.\n", style=YELLOW)
                    return
            content_to_copy = code_blocks[selected_index]
    else:
        content_to_copy = last_msg.content
    
    pyperclip.copy(content_to_copy)
    console.print("Copied to clipboard.\n", style=YELLOW)


def mode_command(
    command: str, console: Console, project_manager: ProjectManager
):
    """Change the current mode."""
    parts = command.split()
    if len(parts) != 2:
        console.print("Usage: /mode <mode>\n", style=YELLOW)
        console.print(
            f"Available modes: {', '.join(Mode.get_values())}\n", style=YELLOW
        )
        return
    mode_str = parts[1]
    try:
        new_mode = Mode.from_string(mode_str)
        project_manager.change_mode(new_mode)
        logger.info(f"Mode changed to {new_mode.value}")
        console.print(f"Mode changed to {new_mode.value}\n", style=YELLOW)
    except ValueError as e:
        logger.error(f"Invalid mode attempted: {mode_str}, error: {e}")
        console.print(
            f"Invalid mode: {mode_str}. Available modes: {', '.join(Mode.get_values())}\n",
            style=YELLOW,
        )


def add_command(
    command: str, console: Console, project_manager: ProjectManager
):
    """Add files to context for the agent/LLM."""
    parts = command.split()
    if len(parts) < 2:
        # Interactive mode: Fuzzy search and select files
        fzf = pyfzf.FzfPrompt()
        all_files = []
        cache_path = project_manager.available_files_cache
        if cache_path.exists():
            with open(cache_path, "r") as f:
                all_files = [line.strip() for line in f if line.strip()]
        else:
            # Fallback to os.walk if cache doesn't exist
            for root, _, files in os.walk(project_manager.project_root):
                root_path = Path(root)
                for file in files:
                    file_path = root_path / file
                    rel_path = file_path.relative_to(
                        project_manager.project_root
                    )
                    all_files.append(str(rel_path))
        selected_files = fzf.prompt(
            all_files, "--multi"
        )  # Multi-select with fuzzy search
        if not selected_files:
            console.print("No files selected.\n", style=YELLOW)
            return
    else:
        # Direct mode: Use provided paths
        selected_files = parts[1:]

    # Validate and add files
    for file_path in selected_files:
        full_path = project_manager.project_root / file_path
        if full_path.is_file():
            project_manager.attach_file(full_path)
            logger.info(f"Attached file: {file_path}")
            console.print(f"Attached file: {file_path}\n", style=YELLOW)
        else:
            logger.warning(f"File not found: {file_path}")
            console.print(f"File not found: {file_path}\n", style=YELLOW)

    # Load objects for attached files
    threading.Thread(
        target=cache_objects,
        args=(
            project_manager.get_attached_files(),
            project_manager.objects_cache,
        ),
    ).start()


def files_command(console: Console, project_manager: ProjectManager):
    """List current files in context."""
    if not project_manager.get_attached_files():
        console.print("No files attached.\n", style=YELLOW)
    else:
        console.print("Attached files:\n", style=YELLOW)
        for i, file_path in enumerate(project_manager.get_attached_files()):
            console.print(f"  {i}: {file_path}\n", style=YELLOW)


def drop_command(
    command: str, console: Console, project_manager: ProjectManager
):
    """Drop files from context by name, or all if no file provided."""
    parts = command.split()
    if len(parts) == 1:
        project_manager.detach_file(remove_all=True)
        logger.info("All files dropped from context")
        console.print("All files dropped from context.\n", style=YELLOW)
    else:
        # File names provided: drop specific files
        for file_name in parts[1:]:
            found = False
            for file_path in project_manager.get_attached_files()[
                :
            ]:  # Copy to avoid modification during iteration
                if file_path.name == file_name:
                    project_manager.detach_file(file_path)
                    logger.info(f"Dropped file: {file_path}")
                    console.print(f"Dropped file: {file_path}\n", style=YELLOW)
                    found = True
                    break
            if not found:
                logger.warning(f"File not found for drop: {file_name}")
                console.print(f"File not found: {file_name}\n", style=YELLOW)

    # Update objects cache after detaching files
    threading.Thread(
        target=cache_objects,
        args=(
            project_manager.get_attached_files(),
            project_manager.objects_cache,
        ),
    ).start()
