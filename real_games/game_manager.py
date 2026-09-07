# ==========================================================
# Melanated AZ Real Games
# game_manager.py
#
# Central multiplayer room manager.
#
# Supports:
#   - Game rooms
#   - Hosts
#   - Multiple players
#   - Private player keys
#   - Scores
#   - Game state
#   - Room expiration
#   - Thread-safe access
#
# IMPORTANT:
# Telegram user IDs are kept internally.
# A random player_key is used by the web game / LiveKit.
# ==========================================================

from __future__ import annotations

import secrets
import threading
import time
import uuid

from dataclasses import dataclass, field
from typing import Any


# ==========================================================
# SETTINGS
# ==========================================================

# Rooms automatically expire after 6 hours without activity.
MAX_ROOM_AGE = 60 * 60 * 6

# Dirty Minds uses up to 20 players.
DEFAULT_MAX_PLAYERS = 20

# ==========================================================
# GAME ROOM
# ==========================================================


@dataclass
class GameRoom:

    # ------------------------------------------------------
    # BASIC ROOM INFORMATION
    # ------------------------------------------------------

    game_id: str
    game_name: str
    room_id: str

    max_players: int = DEFAULT_MAX_PLAYERS
    min_players: int = 1

    created_at: float = field(
        default_factory=time.time
    )

    last_activity: float = field(
        default_factory=time.time
    )

    # ------------------------------------------------------
    # PLAYERS
    #
    # Internal key:
    #     Telegram user ID
    #
    # Each player also receives:
    #     player_key
    #
    # player_key is what the browser uses.
    # ------------------------------------------------------

    players: dict[str, dict[str, Any]] = field(
        default_factory=dict
    )

    # ------------------------------------------------------
    # GAME STATE
    # ------------------------------------------------------

    state: dict[str, Any] = field(
        default_factory=dict
    )

    # ------------------------------------------------------
    # ROOM STATUS
    # ------------------------------------------------------

    started: bool = False

    finished: bool = False

    winner_id: str | None = None

    host_id: str | None = None

    # ======================================================
    # ACTIVITY
    # ======================================================

    def touch(self):
        self.last_activity = time.time()

    # ======================================================
    # ADD PLAYER
    # ======================================================

    def add_player(
        self,
        user_id: str,
        display_name: str,
    ):

        self.touch()

        user_id = str(user_id)

        # --------------------------------------------------
        # Already in room
        # --------------------------------------------------

        if user_id in self.players:
            return self.players[user_id]

        # --------------------------------------------------
        # Room finished
        # --------------------------------------------------

        if self.finished:

            raise ValueError(
                "This game has already finished."
            )

        # --------------------------------------------------
        # Room full
        # --------------------------------------------------

        if len(self.players) >= self.max_players:

            raise ValueError(
                "This game room is full."
            )

        # --------------------------------------------------
        # Generate private browser key
        # --------------------------------------------------

        player_key = secrets.token_urlsafe(24)

        player = {
            "user_id": user_id,
            "player_key": player_key,
            "name": (
                display_name
                or f"Player {user_id}"
            ),
            "joined_at": time.time(),
            "score": 0,
            "host": False,
        }

        # --------------------------------------------------
        # First player becomes host automatically
        # --------------------------------------------------

        if not self.players:

            player["host"] = True
            self.host_id = user_id

        self.players[user_id] = player

        self.touch()

        return player

    # ======================================================
    # REMOVE PLAYER
    # ======================================================

    def remove_player(
        self,
        user_id: str,
    ):

        self.touch()

        user_id = str(user_id)

        removed = self.players.pop(
            user_id,
            None,
        )

        if removed and self.host_id == user_id:

            self._assign_new_host()

        return removed

    # ======================================================
    # ASSIGN NEW HOST
    # ======================================================

    def _assign_new_host(self):

        self.host_id = None

        for player in self.players.values():

            player["host"] = False

        if not self.players:
            return

        # Oldest player becomes host.
        new_host = min(
            self.players.values(),
            key=lambda player: player.get(
                "joined_at",
                time.time(),
            ),
        )

        new_host["host"] = True

        self.host_id = str(
            new_host["user_id"]
        )

    # ======================================================
    # PLAYER COUNT
    # ======================================================

    def player_count(self) -> int:

        return len(self.players)

    # ======================================================
    # GET PLAYER
    # ======================================================

    def get_player(
        self,
        user_id: str,
    ):

        return self.players.get(
            str(user_id)
        )

    # ======================================================
    # GET PLAYER BY PRIVATE KEY
    # ======================================================

    def get_player_by_key(
        self,
        player_key: str,
    ):

        if not player_key:
            return None

        for player in self.players.values():

            if player.get(
                "player_key"
            ) == player_key:

                return player

        return None

    # ======================================================
    # IS HOST
    # ======================================================

    def is_host(
        self,
        user_id: str,
    ) -> bool:

        return (
            self.host_id is not None
            and str(self.host_id)
            == str(user_id)
        )

    # ======================================================
    # IS HOST BY PLAYER KEY
    # ======================================================

    def is_host_key(
        self,
        player_key: str,
    ) -> bool:

        player = self.get_player_by_key(
            player_key
        )

        if not player:
            return False

        return bool(
            player.get("host")
        )

    # ======================================================
    # CAN START
    # ======================================================

    def can_start(self) -> bool:

        return (
            not self.finished
            and len(self.players)
            >= self.min_players
        )

    # ======================================================
    # START
    # ======================================================

    def start(self):

        if not self.can_start():

            raise ValueError(
                "There are not enough players "
                "to start this game."
            )

        self.started = True

        self.touch()

    # ======================================================
    # FINISH
    # ======================================================

    def finish(
        self,
        winner_id: str | None = None,
    ):

        self.finished = True

        self.winner_id = (
            str(winner_id)
            if winner_id is not None
            else None
        )

        self.touch()

    # ======================================================
    # SCORE
    # ======================================================

    def get_score(
        self,
        user_id: str,
    ) -> int:

        player = self.get_player(
            user_id
        )

        if not player:
            return 0

        try:
            return int(
                player.get("score", 0)
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

    # ======================================================
    # ADD SCORE
    # ======================================================

    def add_score(
        self,
        user_id: str,
        points: int = 1,
    ):

        player = self.get_player(
            user_id
        )

        if not player:
            return False

        try:
            points = int(points)
        except (
            TypeError,
            ValueError,
        ):
            points = 0

        current_score = self.get_score(
            user_id
        )

        player["score"] = (
            current_score + points
        )

        self.touch()

        return True

    # ======================================================
    # SET SCORE
    # ======================================================

    def set_score(
        self,
        user_id: str,
        score: int,
    ):

        player = self.get_player(
            user_id
        )

        if not player:
            return False

        try:
            score = int(score)
        except (
            TypeError,
            ValueError,
        ):
            score = 0

        player["score"] = score

        self.touch()

        return True

    # ======================================================
    # RESET SCORES
    # ======================================================

    def reset_scores(self):

        for player in self.players.values():

            player["score"] = 0

        self.touch()

    # ======================================================
    # SAFE PLAYER LIST
    #
    # Does NOT expose Telegram user IDs or player keys.
    # ======================================================

    def public_players(self):

        result = []

        for player in self.players.values():

            result.append(
                {
                    "name": player.get(
                        "name",
                        "Player",
                    ),
                    "score": self.get_score(
                        player.get(
                            "user_id"
                        )
                    ),
                    "host": bool(
                        player.get(
                            "host",
                            False,
                        )
                    ),
                }
            )

        return result

    # ======================================================
    # PUBLIC ROOM DATA
    # ======================================================

    def public_data(self):

        return {
            "room_id": self.room_id,
            "game_id": self.game_id,
            "game_name": self.game_name,
            "player_count": self.player_count(),
            "max_players": self.max_players,
            "min_players": self.min_players,
            "started": self.started,
            "finished": self.finished,
            "winner_id": self.winner_id,
            "players": self.public_players(),
        }


# ==========================================================
# GAME MANAGER
# ==========================================================


class GameManager:

    def __init__(self):

        self.games: dict[
            str,
            GameRoom,
        ] = {}

        self.lock = threading.RLock()

    # ======================================================
    # CREATE ROOM ID
    # ======================================================

    def create_id(self) -> str:

        while True:

            room_id = (
                uuid.uuid4()
                .hex[:8]
                .upper()
            )

            with self.lock:

                if room_id not in self.games:

                    return room_id

    # ======================================================
    # CREATE ROOM
    # ======================================================

    def create(
        self,
        game_id: str,
        game_name: str,
        max_players: int = DEFAULT_MAX_PLAYERS,
        min_players: int = 1,
        state: dict[str, Any] | None = None,
    ) -> GameRoom:

        game_id = str(
            game_id
        ).strip().lower()

        game_name = str(
            game_name
        ).strip()

        max_players = max(
            1,
            int(max_players),
        )

        min_players = max(
            1,
            int(min_players),
        )

        if min_players > max_players:

            raise ValueError(
                "min_players cannot be greater "
                "than max_players."
            )

        room_id = self.create_id()

        room = GameRoom(
            game_id=game_id,
            game_name=game_name,
            room_id=room_id,
            max_players=max_players,
            min_players=min_players,
            state=(
                dict(state)
                if state
                else {}
            ),
        )

        with self.lock:

            self.games[
                room_id
            ] = room

        return room

    # ======================================================
    # GET ROOM
    # ======================================================

    def get(
        self,
        room_id: str,
    ) -> GameRoom | None:

        if not room_id:
            return None

        room_id = str(
            room_id
        ).strip().upper()

        with self.lock:

            room = self.games.get(
                room_id
            )

            if room:

                room.touch()

            return room

    # ======================================================
    # REMOVE ROOM
    # ======================================================

    def remove(
        self,
        room_id: str,
    ):

        if not room_id:
            return

        room_id = str(
            room_id
        ).strip().upper()

        with self.lock:

            return self.games.pop(
                room_id,
                None,
            )

    # ======================================================
    # LIST ROOMS
    # ======================================================

    def list_rooms(
        self,
        game_id: str | None = None,
    ) -> list[GameRoom]:

        with self.lock:

            rooms = list(
                self.games.values()
            )

            if game_id:

                game_id = str(
                    game_id
                ).strip().lower()

                rooms = [
                    room
                    for room in rooms
                    if room.game_id
                    == game_id
                ]

            return rooms

    # ======================================================
    # FIND ROOM FOR PLAYER
    # ======================================================

    def find_player_room(
        self,
        user_id: str,
        game_id: str | None = None,
    ) -> GameRoom | None:

        user_id = str(user_id)

        if game_id:
            game_id = str(
                game_id
            ).strip().lower()

        with self.lock:

            for room in self.games.values():

                if game_id and (
                    room.game_id
                    != game_id
                ):
                    continue

                if user_id in room.players:

                    room.touch()

                    return room

        return None

    # ======================================================
    # FIND ROOM BY PLAYER KEY
    # ======================================================

    def find_room_by_player_key(
        self,
        player_key: str,
    ) -> GameRoom | None:

        if not player_key:
            return None

        with self.lock:

            for room in self.games.values():

                if room.get_player_by_key(
                    player_key
                ):

                    room.touch()

                    return room

        return None

    # ======================================================
    # CLEANUP EXPIRED ROOMS
    # ======================================================

    def cleanup(self):

        now = time.time()

        expired = []

        with self.lock:

            for room_id, room in list(
                self.games.items()
            ):

                age = (
                    now
                    - room.last_activity
                )

                if age > MAX_ROOM_AGE:

                    expired.append(
                        room_id
                    )

            for room_id in expired:

                self.games.pop(
                    room_id,
                    None,
                )

        return expired

    # ======================================================
    # ROOM COUNT
    # ======================================================

    def count(
        self,
        game_id: str | None = None,
    ) -> int:

        return len(
            self.list_rooms(game_id)
        )


# ==========================================================
# GLOBAL GAME MANAGER
# ==========================================================

GAME_MANAGER = GameManager()


# ==========================================================
# END game_manager.py
# ==========================================================
