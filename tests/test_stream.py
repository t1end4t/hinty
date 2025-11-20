from hinty.baml_client import b
from dotenv import load_dotenv

load_dotenv()


# Using a stream:
def example1(receipt: str):
    stream = b.stream.Router(receipt)

    # partial is a Partial type with all Optional fields
    previous = ""
    for partial in stream:
        current = str(partial)
        new_content = current[len(previous) :]
        print(new_content, end="", flush=True)
        previous = current

    # final is the full, original, validated ReceiptInfo type
    final = stream.get_final_response()
    print(f"\nfinal: {final})")


def example2(receipt: str):
    resp = b.Router(receipt)

    print(f"\nfinal: {resp})")


receipt = """
do you think Ho Chi Minh is great leader
"""

if __name__ == "__main__":
    example1(receipt)
