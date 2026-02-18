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

# Example usage:
if __name__ == "__main__":
    my_list = [5, 3, 2, 8, 1]
    target_value = 2
    result = linear_search(my_list, target_value)
    if result != -1:
        print(f"Target found at index: {result}")
    else:
        print("Target not found in the list.")