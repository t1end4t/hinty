from hinty.agents.router import handle_smart_mode
from dotenv import load_dotenv
from hinty.core.context_manager import ContextManager
from baml_py import AbortController
from rich.live import Live
from rich.text import Text

load_dotenv()


def main():
    message = "what you can do"
    ctx = ContextManager()
    controller = AbortController()

    stream = handle_smart_mode(
        user_message=message,
        conversation_history=[],
        context_manager=ctx,
        controller=controller,
    )

    if stream.response:
        text = Text()
        with Live(text, refresh_per_second=4) as live:
            for partial in stream.response:
                text.append(partial)
                live.update(text)


if __name__ == "__main__":
    main()
