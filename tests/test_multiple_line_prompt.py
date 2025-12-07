#!/usr/bin/env python
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


# Custom key bindings: Enter to accept, Shift+Enter to insert newline
bindings = KeyBindings()


@bindings.add("enter")
def _(event):
    event.current_buffer.validate_and_handle()


@bindings.add("shift+enter")
def _(event):
    event.current_buffer.insert_text("\n")


if __name__ == "__main__":
    print("Press [Enter] to accept input, [Shift+Enter] to add a new line.")
    answer = prompt(
        "Multiline input: ",
        multiline=True,
        prompt_continuation=prompt_continuation,
        key_bindings=bindings,
    )
    print(f"You said: {answer}")
