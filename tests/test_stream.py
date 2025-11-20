import time

from dotenv import load_dotenv

from hinty.baml_client import b

load_dotenv()


def example1(receipt: str):
    start_time = time.time()
    stream = b.stream.Router(receipt)

    previous = ""
    first_partial_time = None

    for partial in stream:
        if first_partial_time is None:
            first_partial_time = time.time() - start_time
            print("[LOG] First content received, streaming...\n")

        current = str(partial)
        new_content = current[len(previous) :]

        if new_content:
            print(new_content, end="", flush=True)

        previous = current

    total_time = time.time() - start_time
    print("\n----------")
    print(f"First partial: {first_partial_time:.3f}s")
    print(f"Total time: {total_time:.3f}s")


def example2(receipt: str):
    stream = b.stream.Router(receipt)

    print("[LOG] Starting stream with timing for each partial...\n")

    partial_count = 0
    last_time = time.time()

    for partial in stream:
        current_time = time.time()
        delta = current_time - last_time
        partial_count += 1
        print(f"Partial {partial_count}: {delta:.3f}s")
        last_time = current_time

    print("----------")
    print(f"Total partials: {partial_count}")


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
    # example2(message)
    # example3(message)
