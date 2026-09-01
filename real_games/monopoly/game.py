# ==========================================================
# Melanated AZ Bot
# REAL GAMES - MONOPOLY
#
# Original Monopoly-style game mechanics.
# ==========================================================

import random
import uuid


BOARD = [
    {"name": "START", "price": 0, "rent": 0},

    {"name": "Copper Street", "price": 60, "rent": 2},
    {"name": "Community Chest", "price": 0, "rent": 0},
    {"name": "Desert Avenue", "price": 60, "rent": 4},
    {"name": "Income Tax", "price": 0, "rent": 0},
    {"name": "Central Bank", "price": 200, "rent": 0},

    {"name": "Cactus Road", "price": 100, "rent": 6},
    {"name": "Chance", "price": 0, "rent": 0},
    {"name": "Sunset Boulevard", "price": 100, "rent": 6},
    {"name": "Mountain View", "price": 120, "rent": 8},
    {"name": "JAIL", "price": 0, "rent": 0},

    {"name": "Phoenix Avenue", "price": 140, "rent": 10},
    {"name": "Electric Company", "price": 150, "rent": 0},
    {"name": "Tempe Street", "price": 140, "rent": 10},
    {"name": "Scottsdale Road", "price": 160, "rent": 12},
    {"name": "Desert Works", "price": 200, "rent": 0},

    {"name": "Mesa Avenue", "price": 180, "rent": 14},
    {"name": "Community Chest", "price": 0, "rent": 0},
    {"name": "Tucson Boulevard", "price": 180, "rent": 14},
    {"name": "Old Town Road", "price": 200, "rent": 16},
    {"name": "FREE PARKING", "price": 0, "rent": 0},

    {"name": "Black Canyon", "price": 220, "rent": 18},
    {"name": "Chance", "price": 0, "rent": 0},
    {"name": "Grand Avenue", "price": 220, "rent": 18},
    {"name": "Camelback Road", "price": 240, "rent": 20},
    {"name": "Transit Hub", "price": 200, "rent": 0},

    {"name": "Broadway", "price": 260, "rent": 22},
    {"name": "Central Avenue", "price": 260, "rent": 22},
    {"name": "Water Works", "price": 150, "rent": 0},
    {"name": "Roosevelt Street", "price": 280, "rent": 24},
    {"name": "GO TO JAIL", "price": 0, "rent": 0},

    {"name": "Red Rock", "price": 300, "rent": 26},
    {"name": "Lake Pleasant", "price": 300, "rent": 26},
    {"name": "Community Chest", "price": 0, "rent": 0},
    {"name": "Paradise Valley", "price": 320, "rent": 28},
    {"name": "Airport", "price": 200, "rent": 0},

    {"name": "Camelback Mountain", "price": 350, "rent": 35},
    {"name": "Chance", "price": 0, "rent": 0},
    {"name": "Downtown Phoenix", "price": 400, "rent": 50},
]


SPECIAL_SPACES = {
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
    def __init__(self, player_id, name, token):
        self.id = player_id
        self.name = name
        self.token = token
        self.position = 0
        self.money = 1500
        self.properties = []
        self.in_jail = False
        self.jail_turns = 0
        self.bankrupt = False

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "token": self.token,
            "position": self.position,
            "money": self.money,
            "properties": self.properties,
            "in_jail": self.in_jail,
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

    def __init__(self, creator_id, creator_name):
        self.id = str(uuid.uuid4())[:8]

        self.players = [
            Player(
                creator_id,
                creator_name,
                self.TOKENS[0],
            )
        ]

        self.current_player_index = 0
        self.started = False
        self.finished = False
        self.winner = None
        self.last_roll = None
        self.message = f"{creator_name} created the game."

    # ------------------------------------------------------
    # PLAYER MANAGEMENT
    # ------------------------------------------------------

    def add_player(self, player_id, name):

        if self.started:
            raise ValueError("The game has already started.")

        if len(self.players) >= 6:
            raise ValueError("The game is full.")

        if any(p.id == player_id for p in self.players):
            return

        token = self.TOKENS[len(self.players)]

        self.players.append(
            Player(
                player_id,
                name,
                token,
            )
        )

        self.message = f"{name} joined the game."

    def start(self):

        if len(self.players) < 2:
            raise ValueError("At least 2 players are required.")

        self.started = True
        self.current_player_index = 0

        self.message = (
            f"{self.players[0].name}'s turn."
        )

    # ------------------------------------------------------
    # TURN MANAGEMENT
    # ------------------------------------------------------

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    def roll(self, player_id):

        if not self.started:
            raise ValueError("Game has not started.")

        if self.finished:
            raise ValueError("Game is over.")

        player = self.current_player

        if player.id != player_id:
            raise ValueError("It is not your turn.")

        if player.bankrupt:
            self.next_turn()
            return

        if player.in_jail:

            player.jail_turns += 1

            if player.jail_turns >= 3:
                player.in_jail = False
                player.jail_turns = 0
                player.money -= 50

                if player.money < 0:
                    self.bankrupt_player(player)

                self.message = (
                    f"{player.name} paid $50 and left jail."
                )

            else:
                self.message = (
                    f"{player.name} is still in jail."
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
            player.position + total
        ) % len(BOARD)

        if player.position < old_position:
            player.money += 200

            self.message = (
                f"{player.name} passed START and "
                f"collected $200."
            )
        else:
            self.message = (
                f"{player.name} rolled {die1} + {die2}."
            )

        self.resolve_space(player)

    # ------------------------------------------------------
    # BOARD LOGIC
    # ------------------------------------------------------

    def resolve_space(self, player):

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

            amount = min(200, player.money)

            player.money -= amount

            self.message = (
                f"{player.name} paid ${amount} in tax."
            )

            self.next_turn()
            return

        if name in {"Chance", "Community Chest"}:

            self.draw_card(player, name)
            self.next_turn()
            return

        if name in SPECIAL_SPACES:

            self.next_turn()
            return

        owner = self.property_owner(name)

        if owner and owner.id != player.id:

            rent = space["rent"]

            player.money -= rent
            owner.money += rent

            self.message = (
                f"{player.name} paid ${rent} rent "
                f"to {owner.name}."
            )

            if player.money < 0:
                self.bankrupt_player(player)

            self.next_turn()

        elif not owner:

            self.message = (
                f"{player.name} landed on "
                f"{name}. It costs ${space['price']}."
            )

            # Do not automatically buy.
            # Browser displays BUY button.

        else:
            self.next_turn()

    # ------------------------------------------------------
    # PROPERTY
    # ------------------------------------------------------

    def property_owner(self, property_name):

        for player in self.players:

            if property_name in player.properties:
                return player

        return None

    def buy_property(self, player_id):

        player = self.current_player

        if player.id != player_id:
            raise ValueError("It is not your turn.")

        space = BOARD[player.position]

        if space["name"] in SPECIAL_SPACES:
            raise ValueError("This space cannot be purchased.")

        if self.property_owner(space["name"]):
            raise ValueError("This property is already owned.")

        price = space["price"]

        if player.money < price:
            raise ValueError("You cannot afford this property.")

        player.money -= price
        player.properties.append(space["name"])

        self.message = (
            f"{player.name} bought "
            f"{space['name']} for ${price}."
        )

        self.next_turn()

    # ------------------------------------------------------
    # CARDS
    # ------------------------------------------------------

    def draw_card(self, player, deck):

        cards = [

            ("Collect $100.", 100),
            ("Pay $50.", -50),
            ("Collect $150.", 150),
            ("Pay $100.", -100),
            ("Collect $50 from the bank.", 50),
        ]

        text, amount = random.choice(cards)

        player.money += amount

        self.message = (
            f"{player.name}: {text}"
        )

        if player.money < 0:
            self.bankrupt_player(player)

    # ------------------------------------------------------
    # BANKRUPTCY
    # ------------------------------------------------------

    def bankrupt_player(self, player):

        player.bankrupt = True

        player.money = 0

        self.message = (
            f"{player.name} is bankrupt!"
        )

        active = [
            p for p in self.players
            if not p.bankrupt
        ]

        if len(active) == 1:

            self.finished = True
            self.winner = active[0].name

            self.message = (
                f"🏆 {self.winner} wins the game!"
            )

    # ------------------------------------------------------
    # NEXT TURN
    # ------------------------------------------------------

    def next_turn(self):

        if self.finished:
            return

        if len([
            p for p in self.players
            if not p.bankrupt
        ]) <= 1:
            return

        for _ in range(len(self.players)):

            self.current_player_index = (
                self.current_player_index + 1
            ) % len(self.players)

            player = self.current_player

            if not player.bankrupt:
                self.message = (
                    f"{player.name}'s turn."
                )
                break

    # ------------------------------------------------------
    # STATE
    # ------------------------------------------------------

    def state(self):

        return {
            "id": self.id,
            "started": self.started,
            "finished": self.finished,
            "winner": self.winner,
            "message": self.message,
            "last_roll": self.last_roll,
            "current_player": self.current_player.id
            if self.started and self.players
            else None,
            "players": [
                p.to_dict()
                for p in self.players
            ],
            "board": BOARD,
        }


# Global game rooms.
GAMES = {}


def create_game(player_id, player_name):

    game = MonopolyGame(
        player_id,
        player_name,
    )

    GAMES[game.id] = game

    return game


def get_game(game_id):

    return GAMES.get(game_id)
