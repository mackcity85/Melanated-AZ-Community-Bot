"""
Central manager for Real Games.

Game rooms are kept separate from the existing Games package.
"""

import threading
import uuid


class GameManager:
    def __init__(self):
        self.games = {}
        self.lock = threading.RLock()

    def create(self, game):
        with self.lock:
            self.games[game.game_id] = game
        return game

    def get(self, game_id):
        with self.lock:
            return self.games.get(game_id)

    def remove(self, game_id):
        with self.lock:
            self.games.pop(game_id, None)

    def create_id(self):
        return uuid.uuid4().hex[:8].upper()


GAME_MANAGER = GameManager()
