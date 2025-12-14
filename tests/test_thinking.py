from hinty.baml_client import b
from baml_py import Collector

from dotenv import load_dotenv

load_dotenv()

# Create a collector with optional name
collector = Collector(name="my-collector")

# Use it with a function call
result = b.TestThinking(
    "why human exist ?", baml_options={"collector": collector}
)

# Access logging information
# print(collector.last.usage)  # Print usage metrics
# print(collector.last.raw_llm_response)  # Print final response as string
# since there may be retries, print the last http response received
print(collector.last.calls[-1].http_response)
