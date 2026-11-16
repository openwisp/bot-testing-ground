"""Slug helpers."""


def slugify(text: str) -> str:
    """Return a lowercase slug with words joined by dashes."""
    return "-".join(text.lower().split())
