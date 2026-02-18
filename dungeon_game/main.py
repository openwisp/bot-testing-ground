#!/usr/bin/env python3
from game import Game


def main():
    print("=" * 40)
    print("   🏰 DUNGEON ADVENTURE 🏰")
    print("=" * 40)

    name = input("Enter your name, adventurer: ").strip() or "Hero"
    game = Game(name)

    print(f"\nWelcome, {name}! Find the treasure and escape!")
    print("Type 'help' for commands.\n")
    game.look()

    while game.running:
        try:
            cmd = input("\n> ").strip()
            if cmd == "help":
                print("Commands: look, go <dir>, take <item>, status, quit")
            else:
                game.process_command(cmd)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
