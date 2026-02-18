class Player:
    def __init__(self, name):
        self.name = name
        self.health = 100
        self.inventory = []
        self.position = "entrance"

    def take_damage(self, amount):
        self.health -= amount
        return self.health > 0

    def heal(self, amount):
        self.health = min(100, self.health + amount)

    def add_item(self, item):
        self.inventory.append(item)

    def has_item(self, item):
        return item in self.inventory

    def __str__(self):
        return f"{self.name} | HP: {self.health} | Items: {', '.join(self.inventory) or 'None'}"
