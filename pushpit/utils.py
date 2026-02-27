"""Utility functions for common operations."""

import random
import string
from datetime import datetime


def generate_random_string(length: int = 10) -> str:
    """Generate a random alphanumeric string."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def get_current_timestamp() -> str:
    """Get the current timestamp as a formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9/5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32) * 5/9


def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


def fibonacci(n: int) -> list[int]:
    """Generate Fibonacci sequence up to n numbers."""
    if n <= 0:
        return []
    if n == 1:
        return [0]
    
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq


def word_count(text: str) -> dict[str, int]:
    """Count occurrences of each word in a string."""
    words = text.lower().split()
    counts = {}
    for word in words:
        word = word.strip('.,!?;:')
        counts[word] = counts.get(word, 0) + 1
    return counts


if __name__ == "__main__":
    print("=== Utils Demo ===\n")
    
    print(f"Random string: {generate_random_string(8)}")
    print(f"Timestamp: {get_current_timestamp()}")
    print(f"25°C = {celsius_to_fahrenheit(25):.1f}°F")
    print(f"77°F = {fahrenheit_to_celsius(77):.1f}°C")
    print(f"Is 17 prime? {is_prime(17)}")
    print(f"Fibonacci(10): {fibonacci(10)}")
    print(f"Word count: {word_count('hello world hello python')}")