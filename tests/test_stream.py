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
    is_first_partial = True

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

            # Use faster delay for first partial to compensate for longer wait
            delay = 0.001 if is_first_partial else 0.01
            smooth_print(new_content, delay=delay)
            is_first_partial = False

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
