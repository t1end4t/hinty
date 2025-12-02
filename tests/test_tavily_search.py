from dotenv import load_dotenv

from hinty.tools.search_web import tool_search_web

load_dotenv()

if __name__ == "__main__":
    a = tool_search_web("lastest result of Arsenal football team")

    print(a)
