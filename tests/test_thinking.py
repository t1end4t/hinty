import asyncio
import json
from hinty.baml_client.async_client import BamlAsyncClient
from baml_py import baml_py
from dotenv import load_dotenv
  
load_dotenv()
  
  
def extract_thinking(reason: str, log: baml_py.FunctionLog):
    thinking_content = ""
  
    if log and log.calls:
        last_call = log.calls[-1]
  
        # Check if it's a streaming call
        if hasattr(last_call, "sse_responses"):
            sse_responses = last_call.sse_responses()
            if sse_responses:
                for response in sse_responses:
                    try:
                        data = json.loads(response.text)
                        if "delta" in data and "thinking" in data["delta"]:
                            thinking_content += data["delta"]["thinking"]
                    except (json.JSONDecodeError, AttributeError):
                        pass
  
    if thinking_content:
        print(f"Thinking content: {thinking_content}")
  
  
async def main():
    b = BamlAsyncClient()
    # Use with streaming function
    stream = b.stream.TestThinking(
        "Write a story about AI", baml_options={"on_tick": extract_thinking}
    )
  
    async for msg in stream:
        pass
  
    result = await stream.get_final_response()
    print(result)
  
  
if __name__ == "__main__":
    asyncio.run(main())
