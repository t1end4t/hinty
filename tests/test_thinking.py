import asyncio
import base64
import json
from hinty.baml_client.async_client import b
from baml_py import baml_py
from dotenv import load_dotenv
  
load_dotenv()
  
  
def on_tick(reason: str, log: baml_py.FunctionLog):
    print(f"Tick received: {reason}")
    print(f"Function calls: {len(log.calls) if log else 0}")
  
  
# async def main():
#     # Use with async function
#     result = await b.TestThinking(
#         "Hello world", baml_options={"on_tick": on_tick}
#     )
  
#     print(result)
  
  
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
                        # print(data)  # Commented out to avoid printing the full data
                        if "delta" in data and "reasoning_details" in data["delta"]:
                            for detail in data["delta"]["reasoning_details"]:
                                if detail.get("type") == "reasoning.encrypted":
                                    encrypted_data = detail.get("data", "")
                                    # Attempt to base64 decode the encrypted data
                                    try:
                                        decoded_bytes = base64.b64decode(encrypted_data)
                                        decoded_text = decoded_bytes.decode('utf-8')
                                        thinking_content += decoded_text
                                    except Exception as e:
                                        # If decoding fails, append the raw data
                                        thinking_content += encrypted_data
                    except (json.JSONDecodeError, AttributeError):
                        pass
  
    if thinking_content:
        print(f"Thinking content: {thinking_content}")
  
  
async def main():
    # Use with streaming function
    stream = b.stream.TestThinking(
        "who are you", baml_options={"on_tick": extract_thinking}
    )
  
    async for msg in stream:
        pass
  
    result = await stream.get_final_response()
    print(result)
  
  
if __name__ == "__main__":
    asyncio.run(main())
