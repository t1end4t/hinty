import threading
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
    partial_count = 0
    buffered_content = ""

    for partial in stream:
        if first_partial_time is None:
            first_partial_time = time.time() - start_time

        current = str(partial)
        new_content = current[len(previous) :]

        if new_content:
            partial_count += 1

            # Buffer first 5 partials
            if partial_count <= 5:
                buffered_content += new_content
                if partial_count == 5:
                    print("[LOG] First content received, streaming...\n")
                    print(
                        f"[LOG] Printing buffered content from first 5 partials\n"
                    )
                    # Start smooth printing in a separate thread
                    threading.Thread(target=smooth_print, args=(buffered_content,)).start()
            else:
                # Print subsequent partials immediately
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
