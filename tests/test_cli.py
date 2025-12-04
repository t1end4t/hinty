"""
Basic async CLI example using Click, Rich, and asyncio.
Install dependencies: pip install click rich prompt-toolkit
"""

import asyncio
from typing import List

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


class ChatContext:
    """Simple context manager for chat state."""

    def __init__(self):
        self.conversation: List[dict] = []
        self.running = True

    def add_message(self, role: str, content: str):
        self.conversation.append({"role": role, "content": content})


async def simulate_llm_response(user_input: str) -> str:
    """Simulate an async LLM response with streaming."""
    await asyncio.sleep(0.5)  # Simulate API delay
    return f"Echo: {user_input}"


async def stream_response(text: str, console: Console):
    """Simulate streaming response character by character."""
    console.print("[bold blue]Assistant:[/bold blue]", end=" ")
    for char in text:
        console.print(char, end="")
        await asyncio.sleep(0.02)  # Simulate streaming delay
    console.print("\n")


def handle_command(command: str, context: ChatContext) -> bool:
    """Handle slash commands. Returns True if should continue, False to exit."""
    if command == "/help":
        help_text = """
# Available Commands

- `/help` - Show this help message
- `/history` - Show conversation history
- `/clear` - Clear conversation history
- `/quit` or `/exit` - Exit the chat
        """
        console.print(
            Panel(Markdown(help_text), title="Help", border_style="green")
        )
        return True

    elif command == "/history":
        if not context.conversation:
            console.print("[yellow]No conversation history yet.[/yellow]")
        else:
            console.print(
                Panel.fit("Conversation History", style="bold magenta")
            )
            for i, msg in enumerate(context.conversation, 1):
                role_color = "green" if msg["role"] == "user" else "blue"
                console.print(
                    f"[{role_color}]{i}. {msg['role'].upper()}:[/{role_color}] {msg['content']}"
                )
        return True

    elif command == "/clear":
        context.conversation.clear()
        console.print("[green]Conversation history cleared![/green]")
        return True

    elif command in ["/quit", "/exit"]:
        console.print("[yellow]Goodbye! 👋[/yellow]")
        return False

    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("[dim]Type /help for available commands[/dim]")
        return True


async def process_user_input(user_input: str, context: ChatContext):
    """Process user message and get response."""
    # Add user message to history
    context.add_message("user", user_input)

    # Get simulated LLM response
    response = await simulate_llm_response(user_input)

    # Stream the response
    await stream_response(response, console)

    # Add assistant message to history
    context.add_message("assistant", response)


async def handle_input_loop(session, context):
    while context.running:
        try:
            # Get user input (this is synchronous but that's okay)
            user_input = await asyncio.to_thread(
                session.prompt,
                "You: ",
                # Note: session.prompt is blocking, so we run it in a thread
            )

            if not user_input.strip():
                continue

            # Handle commands
            if user_input.startswith("/"):
                should_continue = handle_command(user_input.strip(), context)
                if not should_continue:
                    break
            else:
                # Process regular message
                await process_user_input(user_input, context)

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /quit to exit properly[/yellow]")
            continue

        except EOFError:
            console.print("\n[yellow]Goodbye! 👋[/yellow]")
            break

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            continue


async def chat_loop():
    """Main chat loop."""
    context = ChatContext()
    session = PromptSession(history=InMemoryHistory())

    # Welcome message
    console.print(
        Panel.fit(
            "[bold cyan]Welcome to Async Chat![/bold cyan]\n"
            "Type [bold]/help[/bold] for commands or start chatting!",
            border_style="cyan",
        )
    )

    await handle_input_loop(session, context)


# Click command setup
@click.command()
@click.option("--debug", is_flag=True, help="Enable debug mode")
def main(debug: bool):
    """
    A basic async chat CLI using Click, Rich, and asyncio.

    This demonstrates the proper way to integrate async code with Click.
    """
    if debug:
        console.print("[dim]Debug mode enabled[/dim]")

    # Run the async chat loop
    # This is the correct way: asyncio.run() at the top level
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted. Goodbye! 👋[/yellow]")


if __name__ == "__main__":
    main()
