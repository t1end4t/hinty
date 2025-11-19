import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


# Minimal LLM chat interface - for now, just responds with "Hello" to any input
async def chat():
    session = PromptSession()
    style = Style.from_dict(
        {
            "prompt": "bold cyan",
        }
    )

    console.print(
        Panel.fit(
            "Welcome to the LLM Chat CLI! Type 'exit' to quit.",
            title="Hinty CLI",
            border_style="blue",
        )
    )

    while True:
        try:
            user_input = await session.prompt_async("You: ", style=style)
            if user_input.lower() == "exit":
                break
            # For now, just respond with "Hello"
            response = "Hello"
            console.print(
                Panel.fit(
                    Text(response, style="green"),
                    title="LLM",
                    border_style="green",
                )
            )
        except KeyboardInterrupt:
            break
        except EOFError:
            break


if __name__ == "__main__":
    asyncio.run(chat())
