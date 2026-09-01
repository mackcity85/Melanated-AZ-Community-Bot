"""
Melanated AZ Bot
Real Games - Game Manager

Central manager for all Real Games.

This manager supports:
- Single-player games
- Multiplayer rooms
- Telegram deep links
- Room expiration
- Player management
- Game-specific state
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


MAX_ROOM_AGE = 60 * 60 * 6  # 6 hours


@dataclass
class GameRoom:
    """
    A live Real Game room.
    """

    game_id: str
    game_name: str
    room_id: str

    max_players: int = 2
    min_players: int = 1

    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    players: dict[str, dict[str, Any]] = field(default_factory=dict)

    state: dict[str, Any] = field(default_factory=dict)

    started: bool = False
    finished: bool = False

    winner_id: str | None = None

    def touch(self):
        self.last_activity = time.time()

    def add_player(
        self,
        user_id: str,
        display_name: str,
    ):
        self.touch()

        if self.finished:
            raise ValueError("This game has already finished.")

        if user_id in self.players:
            return

        if len(self.players) >= self.max_players:
            raise ValueError("This game room is full.")

        self.players[user_id] = {
            "user_id": user_id,
            "name": display_name,
            "joined_at": time.time(),
        }

    def remove_player(self, user_id: str):
        self.touch()
        self.players.pop(user_id, None)

    def player_count(self) -> int:
        return len(self.players)

    def can_start(self) -> bool:
        return (
            not self.finished
            and len(self.players) >= self.min_players
        )

    def start(self):
        if not self.can_start():
            raise ValueError(
                "There are not enough players to start this game."
            )

        self.started = True
        self.touch()

    def finish(self, winner_id: str | None = None):
        self.finished = True
        self.winner_id = winner_id
        self.touch()


class GameManager:
    """
    Thread-safe manager for all Real Game rooms.
    """

    def __init__(self):
        self.games: dict[str, GameRoom] = {}
        self.lock = threading.RLock()

    # ------------------------------------------------------
    # ROOM ID
    # ------------------------------------------------------

    def create_id(self) -> str:
        """
        Create a short human-friendly room ID.
        """

        while True:
            room_id = uuid.uuid4().hex[:8].upper()

            with self.lock:
                if room_id not in self.games:
                    return room_id

    # ------------------------------------------------------
    # CREATE
    # ------------------------------------------------------

    def create(
        self,
        game_id: str,
        game_name: str,
        max_players: int = 2,
        min_players: int = 1,
        state: dict[str, Any] | None = None,
    ) -> GameRoom:

        room_id = self.create_id()

        room = GameRoom(
            game_id=game_id,
            game_name=game_name,
            room_id=room_id,
            max_players=max_players,
            min_players=min_players,
            state=state or {},
        )

        with self.lock:
            self.games[room_id] = room

        return room

    # ------------------------------------------------------
    # GET
    # ------------------------------------------------------

    def get(self, room_id: str) -> GameRoom | None:

        room_id = room_id.upper()

        with self.lock:
            room = self.games.get(room_id)

            if room:
                room.touch()

            return room

    # ------------------------------------------------------
    # REMOVE
    # ------------------------------------------------------

    def remove(self, room_id: str):

        room_id = room_id.upper()

        with self.lock:
            self.games.pop(room_id, None)

    # ------------------------------------------------------
    # LIST
    # ------------------------------------------------------

    def list_rooms(
        self,
        game_id: str | None = None,
    ) -> list[GameRoom]:

        with self.lock:

            rooms = list(self.games.values())

            if game_id:
                rooms = [
                    room
                    for room in rooms
                    if room.game_id == game_id
                ]

            return rooms

    # ------------------------------------------------------
    # CLEANUP
    # ------------------------------------------------------

    def cleanup(self):

        now = time.time()

        expired = []

        with self.lock:

            for room_id, room in self.games.items():

                age = now - room.last_activity

                if age > MAX_ROOM_AGE:
                    expired.append(room_id)

            for room_id in expired:
                self.games.pop(room_id, None)

        return expired


GAME_MANAGER = GameManager()
