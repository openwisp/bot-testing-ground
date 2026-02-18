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


if __name__ == "__main__":
    numbers = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    target = 7
    
    result = binary_search(numbers, target)
    
    if result != -1:
        print(f"Found {target} at index {result}")
    else:
        print(f"{target} not found in the array")
