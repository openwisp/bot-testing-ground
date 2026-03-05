ROOMS = {
    "entrance": {
        "description": "You stand at the dungeon entrance. A torch flickers on the wall.",
        "items": ["torch"],
        "exits": {"north": "hallway"},
    },
    "hallway": {
        "description": "A dark hallway stretches before you. You hear dripping water.",
        "items": [],
        "exits": {"south": "entrance", "east": "armory", "north": "treasure"},
    },
    "armory": {
        "description": "Old weapons line the walls. A rusty sword catches your eye.",
        "items": ["sword"],
        "exits": {"west": "hallway"},
    },
    "treasure": {
        "description": "A chest sits in the center. But a goblin guards it!",
        "items": ["gold"],
        "enemy": {"name": "Goblin", "health": 30, "damage": 15},
        "exits": {"south": "hallway"},
    },
}
