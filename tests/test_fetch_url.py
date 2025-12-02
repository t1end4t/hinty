import asyncio
import sys
from hinty.tools.fetch_url import tool_fetch_url


async def main():
    if len(sys.argv) != 2:
        print("Usage: python fetch_url.py <url>")
        return
    url = sys.argv[1]
    content = await tool_fetch_url(url)
    print(content)


if __name__ == "__main__":
    asyncio.run(main())
