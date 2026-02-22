"""Simple Python program demonstrating basic concepts."""


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}! Welcome to Python."


def factorial(n: int) -> int:
    """
    Calculate the factorial of a non-negative integer.
    
    Args:
        n: A non-negative integer
        
    Returns:
        The factorial of n (n!)
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def calculate_sum(numbers: list[int]) -> int:
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def is_even(number: int) -> bool:
    """Check if a number is even."""
    return number % 2 == 0

def linear_search(arr, target):
    """
    Perform a linear search for the target in the given array.

    Parameters:
    arr (list): The list to search through.
    target: The value to search for.

    Returns:
    int: The index of the target if found, otherwise -1.
    """
    for index in range(len(arr)):
        if arr[index] == target:
            return index
    return -1

def binary_search(arr, target):
    """
    Perform binary search on a sorted array.
    
    Args:
        arr: A sorted list of elements
        target: The element to search for
    
    Returns:
        Index of target if found, -1 otherwise
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

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

    # Linear search example
    my_list = [5, 3, 2, 8, 1]
    target_value = 2
    result = linear_search(my_list, target_value)
    if result != -1:
        print(f"Target found at index: {result}")
    else:
        print("Target not found in the list.")
    
    # Binary search example
    numbers = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    target = 7
    result = binary_search(numbers, target)
    if result != -1:
        print(f"Found {target} at index {result}")
    else:
        print(f"{target} not found in the array")

if __name__ == "__main__":
    main()
