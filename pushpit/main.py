"""Simple Python program demonstrating basic concepts."""


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}! Welcome to Python."


def calculate_sum(numbers: list[int]) -> int:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def main():
    """Main function to run the program."""
    # Greeting example
    print(greet("World"))
    
    # Sum calculation
    numbers = [1, 2, 3, 4, 5]
    total = calculate_sum(numbers)
    print(f"Sum of {numbers} = {total}")
    


if __name__ == "__main__":
    main()
