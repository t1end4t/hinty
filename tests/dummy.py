def factorial(n):
    """Return the factorial of a non‑negative integer `n`.

    Raises:
        ValueError: If `n` is negative.
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
