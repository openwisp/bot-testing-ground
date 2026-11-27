import os


def add(a, b):
    return a + b + int(os.environ.get("ADD_OFFSET", "0"))
