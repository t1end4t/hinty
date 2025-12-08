import asyncio
import os
import re
import threading
from pathlib import Path
from typing import List

import pyperclip
from loguru import logger
from prompt_toolkit.shortcuts import choice
from pyfzf import pyfzf
from rich.console import Console

from ..baml_client.types import ConversationMessage
from ..core.models import Mode
from ..core.project_manager import ProjectManager
from ..utils.cache import cache_objects
from .theme import YELLOW

console = Console()


def help_command(console: Console):
    """Display help information for CLI commands."""
    help_text = (
        "Available commands:\n"
        "/exit         - Exit the CLI\n"
        "/quit         - Quit the CLI\n"
        "/help         - Show this help message\n"
        "/copy         - Copy last response or code blocks (interactive)\n"
        "/clear        - Clear conversation history and chat\n"
        "/files        - List current files in context\n"
        "/add   <file> - Add file to context (or interactive selection if no files)\n"
        "/drop  <file> - Drop file from context by name, or all if no file\n"
        "/mode  <mode> - Change the current mode\n"
        "Type a message to chat with Hinty. Use / to invoke commands."
    )
    from rich.panel import Panel

    panel = Panel(help_text, title="Help", border_style=YELLOW)
    console.print(panel, style=YELLOW)


def clear_command(
    console: Console, conversation_history: List[ConversationMessage]
):
    """Clear conversation history and chat display."""
    conversation_history.clear()
    console.clear()
    console.print("Conversation history and chat cleared.\n", style=YELLOW)


async def copy_command(
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

    # Build options list: full content first, then code blocks
    options = [("full", "Full content")]

    if code_blocks:
        for i, block in enumerate(code_blocks):
            # Get first line or first 50 chars as preview
            first_line = block.splitlines()[0] if block.splitlines() else block
            preview = first_line[:50]
            if len(first_line) > 50:
                preview += "..."
            options.append((str(i), f"Code block {i + 1}: {preview}"))

    # Show single choice menu
    try:
        selected = await asyncio.to_thread(
            choice,
            message="What to copy?",
            options=options,
        )
    except KeyboardInterrupt:
        console.print("Copy cancelled.\n", style=YELLOW)
        return

    # Determine content to copy
    if selected == "full":
        content_to_copy = last_msg.content
    else:
        # selected is the index of the code block
        content_to_copy = code_blocks[int(selected)]

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


async def add_command(
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
        selected_files = await asyncio.to_thread(
            fzf.prompt, all_files, "--multi"
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
