from hinty.baml_client.async_client import b
from baml_py.errors import BamlAbortError
from dotenv import load_dotenv


# Python doesn't have a native abort controller construct,
# so BAML provides a custom implementation
from baml_py import AbortController
import asyncio

load_dotenv()
# Will cancel after 5 seconds, once its used.
controller = AbortController(timeout_ms=5000)
# one can also manually call abort:
controller.abort()
# once aborted, the controller will forever remain in an an aborted state.

text = "who are you"


async def run_with_timeout():
    try:
        result = await b.Router(
            text, baml_options={"abort_controller": controller}
        )

        print(result)
    except BamlAbortError:
        print("Operation was cancelled")
