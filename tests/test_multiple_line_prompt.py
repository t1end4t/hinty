#!/usr/bin/env python
import subprocess
from PIL import Image
import io
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings


def prompt_continuation(width, line_number, wrap_count):
    """
    The continuation: display line numbers and '->' before soft wraps.

    Notice that we can return any kind of formatted text from here.

    The prompt continuation doesn't have to be the same width as the prompt
    which is displayed before the first line, but in this example we choose to
    align them. The `width` input that we receive here represents the width of
    the prompt.
    """
    if wrap_count > 0:
        return " " * (width - 3) + "-> "
    else:
        text = ("- %i - " % (line_number + 1)).rjust(width)
        return HTML("<strong>%s</strong>") % text


def get_clipboard_image():
    """Get image from clipboard if available."""
    try:
        result = subprocess.run(
            ['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'],
            capture_output=True
        )
        if result.returncode == 0:
            img = Image.open(io.BytesIO(result.stdout))
            return img
        else:
            return None
    except Exception:
        return None


# Custom key bindings: Enter to accept, Shift+Enter to insert newline
bindings = KeyBindings()


@bindings.add("enter")
def _(event):
    event.current_buffer.validate_and_handle()


@bindings.add("escape", "enter")
def _(event):
    event.current_buffer.insert_text("\n")


@bindings.add("c-i")  # Ctrl+I to paste image from clipboard
def _(event):
    img = get_clipboard_image()
    if img:
        img.save('pasted_image.png')
        event.current_buffer.insert_text('[Image pasted: pasted_image.png]\n')
    else:
        event.current_buffer.insert_text('[No image in clipboard]\n')


if __name__ == "__main__":
    print("Press [Enter] to accept input, [Shift+Enter] to add a new line, [Ctrl+I] to paste image.")
    answer = prompt(
        "Multiline input: ",
        multiline=True,
        prompt_continuation=prompt_continuation,
        key_bindings=bindings,
    )
    print(f"You said: {answer}")
