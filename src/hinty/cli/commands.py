import re
from typing import List

from loguru import logger
from prompt_toolkit.completion import (
    CompleteEvent,
    Completer,
    Completion,
    FuzzyCompleter,
    FuzzyWordCompleter,
    PathCompleter,
)
from prompt_toolkit.document import Document
from rich.console import Console

from ..baml_client.types import ConversationMessage
from ..core.models import Mode
from ..core.project_manager import ProjectManager
from .theme import YELLOW
from .utils import (
    add_command,
    clear_command,
    copy_command,
    drop_command,
    files_command,
    help_command,
    mode_command,
)

commands = [
    "/add",
    "/clear",
    "/copy",
    "/drop",
    "/exit",
    "/files",
    "/help",
    "/mode",
    "/quit",
]


class CommandCompleter(Completer):
    def __init__(
        self,
        commands,
        project_manager: ProjectManager,
        conversation_history: List[ConversationMessage],
    ):
        self.commands = commands
        self.project_manager = project_manager
        self.conversation_history = conversation_history
        self.path_completer = FuzzyCompleter(PathCompleter())

    def _get_add_completions(
        self, document: Document, complete_event: CompleteEvent
    ):
        text = document.text_before_cursor
        path_part = text[len("/add ") :]

        all_files = []
        cache_path = self.project_manager.available_files_cache
        if cache_path.exists():
            with open(cache_path, "r") as f:
                all_files = [line.strip() for line in f if line.strip()]

        word_document = Document(path_part, len(path_part))
        completer = FuzzyWordCompleter(all_files)
        yield from completer.get_completions(word_document, complete_event)

    def _get_drop_completions(
        self, document: Document, complete_event: CompleteEvent
    ):
        text = document.text_before_cursor
        word = text[len("/drop ") :]
        names = [f.name for f in self.project_manager.get_attached_files()]
        word_document = Document(word, len(word))
        completer = FuzzyWordCompleter(names)
        yield from completer.get_completions(word_document, complete_event)

    def _get_mode_completions(
        self, document: Document, complete_event: CompleteEvent
    ):
        text = document.text_before_cursor
        word = text[len("/mode ") :]
        modes = Mode.get_values()
        word_document = Document(word, len(word))
        completer = FuzzyWordCompleter(modes)
        yield from completer.get_completions(word_document, complete_event)

    def _get_object_completions(
        self, document: Document, complete_event: CompleteEvent
    ):
        if not self.project_manager.get_attached_files():
            return
        text = document.text_before_cursor

        if not re.search(r"\s\w{3,}$", text):
            return
        objects = []
        cache_path = self.project_manager.objects_cache
        if cache_path.exists():
            with open(cache_path, "r") as f:
                objects = [line.strip() for line in f if line.strip()]
        word_document = Document(text, len(text))
        completer = FuzzyWordCompleter(objects)
        for completion in completer.get_completions(
            word_document, complete_event
        ):
            yield Completion(
                text=f"`{completion.text}`",
                start_position=completion.start_position,
                display=completion.display,
            )

    def _get_command_completions(self, text: str):
        word = text
        for command in self.commands:
            if command.startswith(word):
                yield Completion(
                    command,
                    start_position=-len(word),
                    display=command,
                )

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ):
        text = document.text_before_cursor

        # If typing /add command, provide path completions
        if text.startswith("/add "):
            yield from self._get_add_completions(document, complete_event)

        # If typing /drop command, provide file name completions
        elif text.startswith("/drop"):
            yield from self._get_drop_completions(document, complete_event)

        # If typing /mode command, provide mode completions
        elif text.startswith("/mode"):
            yield from self._get_mode_completions(document, complete_event)

        # Otherwise, provide command completions
        elif text.startswith("/"):
            yield from self._get_command_completions(text)

        # If not a command and at least 3 characters, provide object completions
        else:
            yield from self._get_object_completions(document, complete_event)


async def handle_command(
    command: str,
    console: Console,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
):
    """Dispatch commands to their handlers."""
    logger.debug(f"Handling command: {command}")
    if command == "/help":
        help_command(console)
    elif command == "/clear":
        clear_command(console, conversation_history)
    elif command.startswith("/copy"):
        await copy_command(console, conversation_history)
    elif command.startswith("/mode"):
        mode_command(command, console, project_manager)
    elif command.startswith("/add"):
        await add_command(command, console, project_manager)
    elif command == "/files":
        files_command(console, project_manager)
    elif command.startswith("/drop"):
        drop_command(command, console, project_manager)
    elif command in ["/exit", "/quit"]:
        logger.info("Exiting CLI")
        console.print("Exiting CLI...\n", style=YELLOW)
        raise SystemExit
    else:
        logger.warning(f"Unknown command: {command}")
        console.print(f"Unknown command: {command}\n", style=YELLOW)
