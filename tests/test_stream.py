import time
from hinty.baml_client import b
from dotenv import load_dotenv

load_dotenv()


# Using a stream:
def example1(receipt: str):
    start_time = time.time()
    stream = b.stream.Router(receipt)

    # partial is a Partial type with all Optional fields
    previous = ""
    first_partial_time = None
    for partial in stream:
        if first_partial_time is None:
            first_partial_time = time.time() - start_time

        current = str(partial)
        new_content = current[len(previous) :]
        print(new_content, end="", flush=True)
        previous = current

    # final is the full, original, validated ReceiptInfo type
    # final = stream.get_final_response()
    total_time = time.time() - start_time
    # print(f"\nfinal: {final})")
    print("----------")
    print(f"First partial: {first_partial_time:.3f}s")
    print(f"Total time: {total_time:.3f}s")


def example2(receipt: str):
    start_time = time.time()
    resp = b.Router(receipt)
    total_time = time.time() - start_time

    # print(f"\nfinal: {resp})")
    print("----------")
    print(f"Total time: {total_time:.3f}s")


message = """
do you think Ho Chi Minh is great leader
"""

if __name__ == "__main__":
    example1(message)
    example2(message)
