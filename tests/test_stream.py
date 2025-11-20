import time

from dotenv import load_dotenv

from hinty.baml_client import b

load_dotenv()


def smooth_print(text, delay=0.01):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)


def example1(receipt: str):
    start_time = time.time()
    stream = b.stream.Router(receipt)

    previous = ""
    first_partial_time = None
    first_token_printed = False

    for partial in stream:
        if first_partial_time is None:
            first_partial_time = time.time() - start_time

        current = str(partial)
        new_content = current[len(previous) :]

        # Print immediately with smooth animation
        if new_content:
            if not first_token_printed:
                print("[LOG] First content received, streaming...\n")
                first_token_printed = True
            smooth_print(new_content)

        previous = current

    total_time = time.time() - start_time
    print("\n----------")
    print(f"First partial: {first_partial_time:.3f}s")
    print(f"Total time: {total_time:.3f}s")


def example2(receipt: str):
    start_time = time.time()
    stream = b.stream.Router(receipt)

    print("[LOG] Starting stream with timing for each partial...\n")

    for partial in stream:
        elapsed = time.time() - start_time
        print(f"[{elapsed:.3f}s] Partial received: {partial}")

    total_time = time.time() - start_time
    print("----------")
    print(f"Total time: {total_time:.3f}s")


def example3(receipt: str):
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
    example3(message)
