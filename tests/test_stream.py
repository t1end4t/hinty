from hinty.agents.router import handle_smart_mode
from dotenv import load_dotenv
from hinty.core.context_manager import ContextManager
from baml_py import AbortController

load_dotenv()


def main():
    full_response = ""
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
        for partial in stream.response:
            full_response += partial
            print(full_response)


if __name__ == "__main__":
    main()
