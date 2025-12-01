def factorial(n):
    if n < 0:
        raise ValueError("factorial() not defined for negative values")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def hello_world():
    """Return a greeting string."""
    print("Bye some one")


def hello_world_again():
    """Return a greeting string."""
    return "Hello, World!"


def add_two_numbers(a, b):
    """Add two numbers and print the result."""
    try:
        a = float(a)
        b = float(b)
    except ValueError:
        print("Invalid input")
        return
    print(a + b)

class Example:
    """A simple example class."""

    def __init__(self, value):
        self.value = value

    def greet(self):
        """Return a greeting using the stored value."""
        return f"Hello, {self.value}!"
