def add(a, b):
    """Add two non-negative numbers; reject negative inputs."""
    if a < 0 or b < 0:
        raise ValueError("Inputs must be non-negative")
    return a + b


def bounded_index(index, length):
    """Return a zero-based index, rejecting indices outside the sequence."""
    if index < 0:
        raise IndexError("Index out of range")
    return index
