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
WELCOME_MESSAGE = "Welcome to the Hinty CLI! Press Enter on an empty line to quit."
PROMPT_TEXT = ">> "
REFRESH_RATE = 4
  
  
def setup_session() -> PromptSession:
    """Set up the prompt session with completer and style."""
    logger.info("Setting up prompt session")
    completer = CommandCompleter(commands)
    session = PromptSession(completer=completer, complete_while_typing=True)
    logger.info("Prompt session setup complete")
    return session
  
  
def print_welcome():
    """Print the welcome panel."""
    logger.info("Printing welcome message")
    console.print(
        Panel.fit(
            WELCOME_MESSAGE,
            title="Hinty CLI",
            border_style="blue",
        )
    )
  
  
def initialize_conversation() -> tuple[List[ConversationMessage], ContextManager]:
    """Initialize conversation history and context manager."""
    logger.info("Initializing conversation")
    conversation_history: List[ConversationMessage] = []
    context_manager = ContextManager()
    console.print(f"Current directory: {context_manager.pwd_path}")
    logger.info("Conversation initialized")
    return conversation_history, context_manager
  
  
def display_stream_response(stream, console: Console) -> str:
    """Display streaming response and return full response."""
    logger.info("Starting stream display")
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
        logger.info("Stream display complete")
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
    logger.info("Processing user message")
    user_message = ConversationMessage(role="user", content=user_input)
    conversation_history.append(user_message)
    try:
        stream = b.stream.Router(
            user_input, conversation_history=conversation_history
        )
        full_response = display_stream_response(stream, console)
        assistant_message = ConversationMessage(
            role="assistant", content=full_response
        )
        conversation_history.append(assistant_message)
        logger.info("User message processed")
    except Exception as e:
        logger.error(f"Error processing user message: {e}")
        raise
  
  
def handle_input_loop(
    session: PromptSession,
    conversation_history: List[ConversationMessage],
    context_manager: ContextManager,
) -> None:
    """Handle the main input loop."""
    logger.info("Starting input loop")
    style = catppuccin_mocha_style
    while True:
        try:
            user_input = session.prompt(PROMPT_TEXT, style=style)
            if not user_input:
                break
            if user_input.startswith("/"):
                handle_command(user_input, console, conversation_history)
            else:
                process_user_message(user_input, conversation_history, console)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            break
        except EOFError:
            logger.info("EOF received")
            break
        except Exception as e:
            logger.error(f"Unexpected error in input loop: {e}")
            break
    logger.info("Input loop ended")
  
  
# Minimal LLM chat interface
def chat():
    """Run the chat interface."""
    logger.info("Starting chat")
    session = setup_session()
    print_welcome()
    conversation_history, context_manager = initialize_conversation()
    handle_input_loop(session, conversation_history, context_manager)
    logger.info("Chat ended")
  
  
@click.command()
def create_cli():
    """Create and run the CLI."""
    logger.info("Creating CLI")
    chat()
    logger.info("CLI created")
