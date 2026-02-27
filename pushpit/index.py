"""Random utility functions and examples."""

import random
import string


def generate_random_string(length: int = 10) -> str:
    """Generate a random alphanumeric string."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def roll_dice(sides: int = 6) -> int:
    """Roll a dice with specified number of sides."""
    return random.randint(1, sides)


def shuffle_list(items: list) -> list:
    """Return a shuffled copy of the list."""
    shuffled = items.copy()
    random.shuffle(shuffled)
    return shuffled


def pick_random(items: list, count: int = 1):
    """Pick random items from a list."""
    if count == 1:
        return random.choice(items)
    return random.sample(items, min(count, len(items)))


def random_color() -> str:
    """Generate a random hex color code."""
    return f"#{random.randint(0, 0xFFFFFF):06x}"


def coin_flip() -> str:
    """Flip a coin."""
    return random.choice(["heads", "tails"])


if __name__ == "__main__":
    print(f"Random string: {generate_random_string(8)}")
    print(f"Dice roll: {roll_dice()}")
    print(f"Shuffled: {shuffle_list([1, 2, 3, 4, 5])}")
    print(f"Random pick: {pick_random(['apple', 'banana', 'cherry'])}")
    print(f"Random color: {random_color()}")
    print(f"Coin flip: {coin_flip()}")
