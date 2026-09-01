"""
Original property-trading board game.

Designed for 2-6 players.
"""

import random

from ..game_manager import GAME_MANAGER


BOARD = [
    {"name": "START", "price": 0, "rent": 0},
    {"name": "Copper Street", "price": 60, "rent": 4},
    {"name": "Community Chest", "price": 0, "rent": 0},
    {"name": "Desert Avenue", "price": 60, "rent": 4},
    {"name": "Income Tax", "price": 0, "rent": 0},
    {"name": "Central Bank", "price": 0, "rent": 0},

    {"name": "Cactus Road", "price": 100, "rent": 6},
    {"name": "Chance", "price": 0, "rent": 0},
    {"name": "Sunset Boulevard", "price": 100, "rent": 6},
    {"name": "Mountain View", "price": 120, "rent": 8},
    {"name": "JAIL", "price": 0, "rent": 0},

    {"name": "Phoenix Avenue", "price": 140, "rent": 10},
    {"name": "Electric Company", "price": 150, "rent": 0},
    {"name": "Tempe Street", "price": 140, "rent": 10},
    {"name": "Scottsdale Road", "price": 160, "rent": 12},
    {"name": "Desert Works", "price": 0, "rent": 0},

    {"name": "Mesa Avenue", "price": 180, "rent": 14},
    {"name": "Community Chest", "price": 0, "rent": 0},
    {"name": "Tucson Boulevard", "price": 180, "rent": 14},
    {"name": "Old Town Road", "price": 200, "rent": 16},
    {"name": "FREE PARKING", "price": 0, "rent": 0},

    {"name": "Black Canyon", "price": 220, "rent": 18},
    {"name": "Chance", "price": 0, "rent": 0},
    {"name": "Grand Avenue", "price": 220, "rent": 18},
    {"name": "Camelback Road", "price": 240, "rent": 20},
    {"name": "Transit Hub", "price": 0, "rent": 0},

    {"name": "Broadway", "price": 260, "rent": 22},
    {"name": "Central Avenue", "price": 260, "rent": 22},
    {"name": "Water Works", "price": 150, "rent": 0},
    {"name": "Roosevelt Street", "price": 280, "rent": 24},
    {"name": "GO TO JAIL", "price": 0, "rent": 0},

    {"name": "Red Rock", "price": 300, "rent": 26},
    {"name": "Lake Pleasant", "price": 300, "rent": 26},
    {"name": "Community Chest", "price": 0, "rent": 0},
    {"name": "Paradise Valley", "price": 320, "rent": 28},
    {"name": "Airport", "price": 0, "rent": 0},

    {"name": "Camelback Mountain", "price": 350, "rent": 35},
    {"name": "Chance", "price": 0, "rent": 0},
    {"name": "Downtown Phoenix", "price": 400, "rent": 50},
]


SPECIAL = {
    "START",
    "Community Chest",
    "Chance",
    "Income Tax",
    "Central Bank",
    "JAIL",
    "Electric Company",
    "Desert Works",
    "FREE PARKING",
    "GO TO JAIL",
    "Transit Hub",
    "Water Works",
    "Airport",
}


class Player:

    def __init__(
        self,
        player_id,
        name,
        token,
    ):

        self.id = str(player_id)
        self.name = name[:40]
        self.token = token

        self.position = 0
        self.money = 1500

        self.properties = []

        self.in_jail = False
        self.jail_turns = 0

        self.bankrupt = False

    def serialize(self):

        return {
            "id": self.id,
            "name": self.name,
            "token": self.token,
            "position": self.position,
            "money": self.money,
            "properties": self.properties,
            "in_jail": self.in_jail,
            "jail_turns": self.jail_turns,
            "bankrupt": self.bankrupt,
        }


class MonopolyGame:

    TOKENS = [
        "👑",
        "🔥",
        "💎",
        "🐍",
        "🦁",
        "⭐",
    ]

    def __init__(
        self,
        creator_id,
        creator_name,
    ):

        self.game_id = GAME_MANAGER.create_id()

        self.players = []

        self.started = False
        self.finished = False

        self.current_index = 0

        self.last_roll = None

        self.message = (
            f"{creator_name} created the game."
        )

        self.winner = None

        self.add_player(
            creator_id,
            creator_name,
        )

    # ------------------------------------------------------
    # PLAYERS
    # ------------------------------------------------------

    def add_player(
        self,
        player_id,
        name,
    ):

        player_id = str(player_id)

        if self.started:
            raise ValueError(
                "The game has already started."
            )

        if len(self.players) >= 6:
            raise ValueError(
                "The game is full."
            )

        if any(
            p.id == player_id
            for p in self.players
        ):
            return

        player = Player(
            player_id,
            name,
            self.TOKENS[len(self.players)],
        )

        self.players.append(player)

        self.message = (
            f"{player.name} joined the game."
        )

    # ------------------------------------------------------
    # START
    # ------------------------------------------------------

    def start(self):

        if self.started:
            return

        if len(self.players) < 2:
            raise ValueError(
                "You need at least 2 players."
            )

        self.started = True

        self.current_index = 0

        self.message = (
            f"{self.current_player.name}'s turn."
        )

    # ------------------------------------------------------
    # CURRENT PLAYER
    # ------------------------------------------------------

    @property
    def current_player(self):

        return self.players[
            self.current_index
        ]

    # ------------------------------------------------------
    # ROLL
    # ------------------------------------------------------

    def roll(
        self,
        player_id,
    ):

        if not self.started:
            raise ValueError(
                "The game has not started."
            )

        if self.finished:
            raise ValueError(
                "The game is over."
            )

        player = self.current_player

        if player.id != str(player_id):
            raise ValueError(
                "It is not your turn."
            )

        if player.in_jail:

            player.jail_turns += 1

            if player.jail_turns >= 3:

                player.in_jail = False
                player.jail_turns = 0

                player.money -= 50

                self.message = (
                    f"{player.name} paid $50 "
                    "and left jail."
                )

            else:

                self.message = (
                    f"{player.name} is in jail. "
                    f"Jail turn {player.jail_turns}/3."
                )

            self.next_turn()

            return

        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)

        total = die1 + die2

        self.last_roll = {
            "die1": die1,
            "die2": die2,
            "total": total,
        }

        old_position = player.position

        player.position = (
            old_position + total
        ) % len(BOARD)

        if player.position < old_position:

            player.money += 200

            self.message = (
                f"{player.name} passed START "
                "and collected $200."
            )

        else:

            self.message = (
                f"{player.name} rolled "
                f"{die1} + {die2}."
            )

        self.resolve_space(player)

    # ------------------------------------------------------
    # SPACE
    # ------------------------------------------------------

    def resolve_space(
        self,
        player,
    ):

        space = BOARD[player.position]

        name = space["name"]

        if name == "GO TO JAIL":

            player.position = 10
            player.in_jail = True
            player.jail_turns = 0

            self.message = (
                f"{player.name} was sent to jail."
            )

            self.next_turn()

            return

        if name == "Income Tax":

            amount = min(
                200,
                player.money,
            )

            player.money -= amount

            self.message = (
                f"{player.name} paid ${amount} "
                "in tax."
            )

            self.next_turn()

            return

        if name in {
            "Chance",
            "Community Chest",
        }:

            self.card(player)

            self.next_turn()

            return

        if name in SPECIAL:

            self.next_turn()

            return

        owner = self.owner_of(name)

        if owner and owner.id != player.id:

            rent = space["rent"]

            player.money -= rent
            owner.money += rent

            self.message = (
                f"{player.name} paid ${rent} rent "
                f"to {owner.name}."
            )

            if player.money < 0:
                self.bankrupt(player)

            self.next_turn()

            return

        if owner is None:

            self.message = (
                f"{player.name} landed on "
                f"{name}. "
                f"Purchase price: ${space['price']}."
            )

            return

        self.next_turn()

    # ------------------------------------------------------
    # BUY
    # ------------------------------------------------------

    def buy(
        self,
        player_id,
    ):

        player = self.current_player

        if player.id != str(player_id):
            raise ValueError(
                "It is not your turn."
            )

        space = BOARD[player.position]

        name = space["name"]

        if name in SPECIAL:
            raise ValueError(
                "This space cannot be purchased."
            )

        if self.owner_of(name):
            raise ValueError(
                "This property is already owned."
            )

        price = space["price"]

        if player.money < price:
            raise ValueError(
                "You cannot afford this property."
            )

        player.money -= price

        player.properties.append(name)

        self.message = (
            f"{player.name} bought "
            f"{name} for ${price}."
        )

        self.next_turn()

    # ------------------------------------------------------
    # CARDS
    # ------------------------------------------------------

    def card(
        self,
        player,
    ):

        cards = [
            ("You found $100.", 100),
            ("You received $150.", 150),
            ("You paid a $50 fee.", -50),
            ("You paid a $100 fee.", -100),
            ("Bank bonus: $75.", 75),
        ]

        text, amount = random.choice(cards)

        player.money += amount

        self.message = (
            f"{player.name}: {text}"
        )

        if player.money < 0:
            self.bankrupt(player)

    # ------------------------------------------------------
    # OWNER
    # ------------------------------------------------------

    def owner_of(
        self,
        property_name,
    ):

        for player in self.players:

            if (
                property_name
                in player.properties
            ):
                return player

        return None

    # ------------------------------------------------------
    # BANKRUPTCY
    # ------------------------------------------------------

    def bankrupt(
        self,
        player,
    ):

        player.bankrupt = True
        player.money = 0

        self.message = (
            f"{player.name} is bankrupt."
        )

        active = [
            p
            for p in self.players
            if not p.bankrupt
        ]

        if len(active) == 1:

            self.finished = True

            self.winner = active[0].name

            self.message = (
                f"🏆 {self.winner} wins!"
            )

    # ------------------------------------------------------
    # NEXT TURN
    # ------------------------------------------------------

    def next_turn(self):

        if self.finished:
            return

        active = [
            p
            for p in self.players
            if not p.bankrupt
        ]

        if len(active) <= 1:
            return

        for _ in range(len(self.players)):

            self.current_index = (
                self.current_index + 1
            ) % len(self.players)

            if not self.current_player.bankrupt:

                self.message = (
                    f"{self.current_player.name}'s turn."
                )

                return

    # ------------------------------------------------------
    # STATE
    # ------------------------------------------------------

    def serialize(self):

        return {
            "game_id": self.game_id,
            "started": self.started,
            "finished": self.finished,
            "winner": self.winner,
            "message": self.message,
            "current_player": (
                self.current_player.id
                if self.started
                else None
            ),
            "last_roll": self.last_roll,
            "players": [
                p.serialize()
                for p in self.players
            ],
            "board": BOARD,
        }
