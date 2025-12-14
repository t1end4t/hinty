import logging
from hinty.tools.fetch_url import tool_fetch_url

logger = logging.getLogger(__name__)


# Usage example
if __name__ == "__main__":
    import asyncio

    a = asyncio.run(tool_fetch_url("https://arxiv.org/abs/1706.03762"))

    print(a)
