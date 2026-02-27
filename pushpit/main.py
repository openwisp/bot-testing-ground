"""Simple Python program demonstrating basic concepts."""

from typing import Optional


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}! Welcome to Python."


def calculate_sum(numbers: list[int]) -> int:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def calculate_average(numbers: list[int]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def is_even(number: int) -> bool:
    """Check if a number is even."""
    return number % 2 == 0


def factorial(n: int) -> int:
    """Calculate factorial of a number recursively."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def find_max(numbers: list[int]) -> Optional[int]:
    """Find the maximum number in a list."""
    if not numbers:
        return None
    return max(numbers)


def find_min(numbers: list[int]) -> Optional[int]:
    """Find the minimum number in a list."""
    if not numbers:
        return None
    return min(numbers)


def reverse_string(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


def is_palindrome(text: str) -> bool:
    """Check if a string is a palindrome."""
    cleaned = text.lower().replace(" ", "")
    return cleaned == cleaned[::-1]


def main():
    """Main function to run the program."""
    print("=" * 40)
    print("Python Demo Program")
    print("=" * 40)
    
    # Greeting example
    print("\n1. Greeting:")
    print(greet("World"))
    
    # Sum and average calculation
    numbers = [1, 2, 3, 4, 5]
    print(f"\n2. Math operations on {numbers}:")
    print(f"   Sum: {calculate_sum(numbers)}")
    print(f"   Average: {calculate_average(numbers):.2f}")
    print(f"   Max: {find_max(numbers)}")
    print(f"   Min: {find_min(numbers)}")
    
    # Factorial
    print("\n3. Factorials:")
    for num in range(1, 6):
        print(f"   {num}! = {factorial(num)}")
    
    # Even/odd check
    print("\n4. Even/Odd check:")
    for num in range(1, 6):
        status = "even" if is_even(num) else "odd"
        print(f"   {num} is {status}")
    
    # String operations
    print("\n5. String operations:")
    word = "Python"
    print(f"   Original: {word}")
    print(f"   Reversed: {reverse_string(word)}")
    
    # Palindrome check
    print("\n6. Palindrome check:")
    test_words = ["radar", "hello", "A man a plan a canal Panama"]
    for word in test_words:
        result = "is" if is_palindrome(word) else "is not"
        print(f"   '{word}' {result} a palindrome")
    
    print("\n" + "=" * 40)


if __name__ == "__main__":
    main()
