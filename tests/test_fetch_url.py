import asyncio
from hinty.tools.fetch_url import tool_fetch_url


async def main():
    url = "https://example.com"
    content = await tool_fetch_url(url)
    print(content)


if __name__ == "__main__":
    asyncio.run(main())
