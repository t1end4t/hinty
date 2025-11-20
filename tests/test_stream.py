from hinty.baml_client import b
from dotenv import load_dotenv

load_dotenv()


# Using a stream:
def example1(receipt: str):
    stream = b.stream.Router(receipt)

    # partial is a Partial type with all Optional fields
    for partial in stream:
        print(str(partial)[-80:])  # Print last 80 chars to show progress

    # final is the full, original, validated ReceiptInfo type
    final = stream.get_final_response()
    print(f"final: {final})")


receipt = """
do you think Ho Chi Minh is great leader
"""

if __name__ == "__main__":
    example1(receipt)
