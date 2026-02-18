from player import Player
from rooms import ROOMS


class Game:
    def __init__(self, player_name):
        self.player = Player(player_name)
        self.running = True

    def get_room(self):
        return ROOMS[self.player.position]

    def look(self):
        room = self.get_room()
        print(f"\n{room['description']}")
        if room["items"]:
            print(f"You see: {', '.join(room['items'])}")
        print(f"Exits: {', '.join(room['exits'].keys())}")

    def move(self, direction):
        room = self.get_room()
        if direction in room["exits"]:
            self.player.position = room["exits"][direction]
            self.look()
            self.check_enemy()
        else:
            print("You can't go that way!")

    def take(self, item):
        room = self.get_room()
        if item in room["items"]:
            room["items"].remove(item)
            self.player.add_item(item)
            print(f"You picked up the {item}.")
        else:
            print("That item isn't here.")

    def check_enemy(self):
        room = self.get_room()
        if "enemy" in room and room["enemy"]:
            enemy = room["enemy"]
            print(f"\n⚔️  A {enemy['name']} attacks you!")
            if self.player.has_item("sword"):
                print("You slay it with your sword!")
                room["enemy"] = None
            else:
                damage = enemy["damage"]
                if not self.player.take_damage(damage):
                    print("You have been defeated...")
                    self.running = False
                else:
                    print(f"You take {damage} damage and flee south!")
                    self.player.position = room["exits"].get("south", "entrance")

    def process_command(self, cmd):
        parts = cmd.lower().split()
        if not parts:
            return

        action = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        if action in ("quit", "q"):
            self.running = False
            print("Thanks for playing!")
        elif action == "look":
            self.look()
        elif action == "status":
            print(self.player)
        elif action in ("go", "move") and arg:
            self.move(arg)
        elif action in ("north", "south", "east", "west"):
            self.move(action)
        elif action in ("take", "get") and arg:
            self.take(arg)
        else:
            print("Commands: look, go <dir>, take <item>, status, quit")
