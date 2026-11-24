def add(a, b):
    return a + b


def percentage(part, total):
    """Return a whole-number percentage between zero and 100."""
    if total == 0:
        return 0
    return round(part * 100 / total)
