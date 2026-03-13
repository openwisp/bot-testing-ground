"""Simple Python program demonstrating basic concepts."""


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}! Welcome to Python."


def calculate_sum(numbers: list[int]) -> int:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def is_even(number: int) -> bool:
    """Check if a number is even."""
    return number % 2 == 0

def factorial(n: int) -> int:
    """Calculate the factorial of a number."""
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)
    


def main():
    """Main function to run the program."""
    # Greeting example
    print(greet("World"))
    
    # Sum calculation
    numbers = [1, 2, 3, 4, 5]
    total = calculate_sum(numbers)
    print(f"Sum of {numbers} = {total}")
    
    # Even/odd check
    for num in range(1, 6):
        status = "even" if is_even(num) else "odd"
        print(f"{num} is {status}")


if __name__ == "__main__":
    main()
