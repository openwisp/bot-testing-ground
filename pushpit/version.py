"""Version helpers."""

VERSION = (1, 2, 0)


def version_string() -> str:
    """Return the version as a dotted string."""
    return ".".join(str(part) for part in VERSION)
