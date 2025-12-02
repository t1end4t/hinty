from tavily import TavilyClient

client = TavilyClient("TAVILY_API_KEY")
response = client.search(query="who is Ho Chi Minh")
print(response)
