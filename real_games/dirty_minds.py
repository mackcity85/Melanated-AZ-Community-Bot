# ==========================================================
# Melanated AZ Real Games
# dirty_minds.py
#
# Multiplayer Dirty Minds game engine.
#
# Features:
#   - Multiplayer rooms
#   - Original clean-answer clues
#   - 10 rounds per game
#   - Synchronized rounds
#   - Server-side answer validation
#   - Score tracking
#   - Host controls
#   - Reveal answers
#   - Next-round controls
#   - Safe public game state
#
# IMPORTANT:
# Answers are NEVER exposed to the browser until reveal.
# ==========================================================

from __future__ import annotations

import random
import re
import time
from typing import Any


# ==========================================================
# GAME SETTINGS
# ==========================================================

TOTAL_ROUNDS = 10
POINTS_PER_CORRECT_ANSWER = 1


# ==========================================================
# ORIGINAL DIRTY MINDS CLUE BANK
#
# These are original clues created for this game.
# The answer to each clue is clean.
# ==========================================================

DIRTY_MINDS_CLUES: list[dict[str, Any]] = [
    {
        "clue": "You put it in your mouth, pull it out, and it comes back wet.",
        "answer": "toothbrush",
        "aliases": ["tooth brush"],
    },
    {
        "clue": "The harder you push it, the deeper it goes.",
        "answer": "button",
        "aliases": ["a button", "the button"],
    },
    {
        "clue": "It gets longer when you pull it.",
        "answer": "rubber band",
        "aliases": ["rubberband"],
    },
    {
        "clue": "You can ride it, but you don't need a saddle.",
        "answer": "bicycle",
        "aliases": ["bike"],
    },
    {
        "clue": "You blow it before you put it in.",
        "answer": "balloon",
        "aliases": ["a balloon"],
    },
    {
        "clue": "It can be hard or soft, and you sleep on it every night.",
        "answer": "pillow",
        "aliases": ["a pillow"],
    },
    {
        "clue": "You grab it when you need to change direction.",
        "answer": "steering wheel",
        "aliases": ["steeringwheel"],
    },
    {
        "clue": "It goes in dry and comes out wet.",
        "answer": "tea bag",
        "aliases": ["teabag"],
    },
    {
        "clue": "You lick it before sticking it somewhere.",
        "answer": "stamp",
        "aliases": ["a stamp"],
    },
    {
        "clue": "It gets hot when you rub it.",
        "answer": "your hands",
        "aliases": ["hands", "my hands", "your hand", "hands"],
    },
    {
        "clue": "You put your fingers in it to make it work.",
        "answer": "glove",
        "aliases": ["a glove"],
    },
    {
        "clue": "It has a head and a shaft but isn't a person.",
        "answer": "golf club",
        "aliases": ["golfclub", "club"],
    },
    {
        "clue": "You push it in and pull it out all day.",
        "answer": "drawer",
        "aliases": ["a drawer"],
    },
    {
        "clue": "It gets wetter the more it dries.",
        "answer": "towel",
        "aliases": ["a towel"],
    },
    {
        "clue": "You sit on it, but it can also be opened.",
        "answer": "toilet",
        "aliases": ["a toilet"],
    },
    {
        "clue": "You put it on your finger before you use it.",
        "answer": "ring",
        "aliases": ["a ring"],
    },
    {
        "clue": "It has two balls but isn't a sport.",
        "answer": "snowman",
        "aliases": ["a snowman"],
    },
    {
        "clue": "You pull it before you push it.",
        "answer": "door handle",
        "aliases": ["doorhandle", "handle"],
    },
    {
        "clue": "You stick it in a hole to open something.",
        "answer": "key",
        "aliases": ["a key"],
    },
    {
        "clue": "You put it in your ear when you want to listen.",
        "answer": "earbud",
        "aliases": ["ear bud", "earphone", "earphones"],
    },
    {
        "clue": "You squeeze it and something comes out.",
        "answer": "toothpaste",
        "aliases": ["tooth paste"],
    },
    {
        "clue": "You put it between your lips before you blow.",
        "answer": "whistle",
        "aliases": ["a whistle"],
    },
    {
        "clue": "It has a handle and you use it to sweep.",
        "answer": "broom",
        "aliases": ["a broom"],
    },
    {
        "clue": "You pull its cord to make it start.",
        "answer": "lawn mower",
        "aliases": ["lawnmower"],
    },
    {
        "clue": "You sit in it and move it with your feet.",
        "answer": "swing",
        "aliases": ["a swing"],
    },
]


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def normalize_answer(value: Any) -> str:
    """
    Normalize an answer for comparison.

    Examples:
        "A Toothbrush!" -> "toothbrush"
        "TOOTH BRUSH"  -> "toothbrush"
        "the pillow"   -> "pillow"
    """

    if value is None:
        return ""

    text = str(value).strip().lower()

    # Remove punctuation.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    # Remove common leading articles.
    text = re.sub(r"^(a|an|the)\s+", "", text)

    # Remove spaces for comparison.
    return text.replace(" ", "")


def _build_answer_keys(clue: dict[str, Any]) -> set[str]:
    """
    Build all accepted normalized answers for a clue.
    """

    keys = {
        normalize_answer(clue.get("answer", "")),
    }

    for alias in clue.get("aliases", []):
        normalized = normalize_answer(alias)
        if normalized:
            keys.add(normalized)

    return {key for key in keys if key}


def answer_is_correct(clue: dict[str, Any], answer: str) -> bool:
    """
    Check a submitted answer against the clue.
    """

    submitted = normalize_answer(answer)

    if not submitted:
        return False

    return submitted in _build_answer_keys(clue)


# ==========================================================
# GAME STATE
# ==========================================================

def create_dirty_minds_state() -> dict[str, Any]:
    """
    Create a brand-new Dirty Minds state.
    """

    return {
        "status": "waiting",

        "round": 0,
        "total_rounds": TOTAL_ROUNDS,

        # Selected clues for this game.
        "rounds": [],

        # Current clue.
        "current_clue": "",
        "current_answer": "",

        # Submitted answers.
        #
        # Key:
        #   player_key
        #
        # Value:
        #   {
        #       "answer": "...",
        #       "correct": True/False,
        #       "submitted_at": timestamp
        #   }
        #
        # This remains server-side.
        "answers": {},

        "revealed": False,

        "round_winner": None,

        "round_started_at": None,

        # Results become available only after reveal.
        "round_results": [],

        # Final winner.
        "winner": None,

        "game_started_at": None,
        "game_finished_at": None,
    }


# ==========================================================
# ROUND CREATION
# ==========================================================

def _select_rounds() -> list[dict[str, Any]]:
    """
    Randomly select the clues for a game.
    """

    count = min(TOTAL_ROUNDS, len(DIRTY_MINDS_CLUES))

    selected = random.sample(DIRTY_MINDS_CLUES, count)

    # Copy dictionaries so the original clue bank
    # can never be modified accidentally.
    return [
        {
            "clue": item["clue"],
            "answer": item["answer"],
            "aliases": list(item.get("aliases", [])),
        }
        for item in selected
    ]


def _load_current_round(room) -> None:
    """
    Load the current round into the room state.
    """

    state = room.state

    round_number = int(state.get("round", 0))

    rounds = state.get("rounds", [])

    if round_number < 1:
        raise ValueError("Invalid round number.")

    if round_number > len(rounds):
        raise ValueError("Round does not exist.")

    current = rounds[round_number - 1]

    state["current_clue"] = current["clue"]
    state["current_answer"] = current["answer"]

    state["answers"] = {}
    state["revealed"] = False
    state["round_winner"] = None
    state["round_results"] = []
    state["round_started_at"] = time.time()

    room.touch()


# ==========================================================
# START GAME
# ==========================================================

def start_game(room) -> dict[str, Any]:
    """
    Start or restart a Dirty Minds game.

    Host validation should be performed by the Flask route.
    """

    if room.player_count() < room.min_players:
        raise ValueError(
            f"At least {room.min_players} players are required."
        )

    rounds = _select_rounds()

    room.state = create_dirty_minds_state()

    room.state["status"] = "playing"
    room.state["round"] = 1
    room.state["total_rounds"] = len(rounds)
    room.state["rounds"] = rounds
    room.state["game_started_at"] = time.time()

    room.started = True
    room.finished = False
    room.winner_id = None

    room.reset_scores()

    _load_current_round(room)

    return public_room_state(room)


# ==========================================================
# SUBMIT ANSWER
# ==========================================================

def submit_answer(
    room,
    player_key: str,
    answer: str,
) -> dict[str, Any]:
    """
    Submit one answer for the current round.

    Each player may submit only once per round.
    """

    player = room.get_player_by_key(player_key)

    if not player:
        raise ValueError("Player is not in this game.")

    state = room.state

    if state.get("status") != "playing":
        raise ValueError("This round is not accepting answers.")

    if state.get("revealed"):
        raise ValueError("The answer has already been revealed.")

    answer = str(answer or "").strip()

    if not answer:
        raise ValueError("Please enter an answer.")

    if len(answer) > 100:
        raise ValueError("Answer is too long.")

    answers = state.setdefault("answers", {})

    if player_key in answers:
        raise ValueError("You already submitted an answer this round.")

    round_number = int(state.get("round", 0))

    rounds = state.get("rounds", [])

    if not round_number or round_number > len(rounds):
        raise ValueError("Invalid current round.")

    clue = rounds[round_number - 1]

    correct = answer_is_correct(clue, answer)

    answers[player_key] = {
        "answer": answer,
        "correct": correct,
        "submitted_at": time.time(),
    }

    # Award the point immediately.
    #
    # A player can only submit once, so this cannot be
    # exploited by repeatedly submitting answers.
    if correct:
        room.add_score(
            player["user_id"],
            POINTS_PER_CORRECT_ANSWER,
        )

        if not state.get("round_winner"):
            state["round_winner"] = player["user_id"]

    room.touch()

    return {
        "success": True,
        "submitted": True,
        "correct": correct,
        "message": (
            "🔥 Correct!"
            if correct
            else "❌ Not quite! Wait for the reveal."
        ),
        "state": public_room_state(
            room,
            player_key=player_key,
        ),
    }


# ==========================================================
# REVEAL ROUND
# ==========================================================

def reveal_round(room) -> dict[str, Any]:
    """
    Reveal the correct answer and all submitted answers.

    Host-only validation should be performed by the Flask route.
    """

    state = room.state

    if state.get("status") != "playing":
        raise ValueError("This round is not active.")

    if state.get("revealed"):
        return public_room_state(room)

    round_number = int(state.get("round", 0))
    rounds = state.get("rounds", [])

    if round_number < 1 or round_number > len(rounds):
        raise ValueError("Invalid current round.")

    clue = rounds[round_number - 1]

    answers = state.get("answers", {})

    results = []

    for player_key, submission in answers.items():
        player = room.get_player_by_key(player_key)

        if not player:
            continue

        results.append(
            {
                "name": player.get("name", "Player"),
                "answer": submission.get("answer", ""),
                "correct": bool(submission.get("correct")),
            }
        )

    # Include players who did not submit.
    submitted_keys = set(answers.keys())

    for player in room.players.values():
        player_key = player.get("player_key")

        if player_key in submitted_keys:
            continue

        results.append(
            {
                "name": player.get("name", "Player"),
                "answer": "",
                "correct": False,
                "did_not_answer": True,
            }
        )

    state["revealed"] = True
    state["status"] = "revealed"
    state["round_results"] = results

    room.touch()

    return public_room_state(room)


# ==========================================================
# NEXT ROUND
# ==========================================================

def next_round(room) -> dict[str, Any]:
    """
    Advance to the next round.

    Host-only validation should be performed by the Flask route.
    """

    state = room.state

    status = state.get("status")

    if status not in {"playing", "revealed"}:
        raise ValueError("The game is not ready for the next round.")

    current_round = int(state.get("round", 0))
    total_rounds = int(
        state.get(
            "total_rounds",
            TOTAL_ROUNDS,
        )
    )

    if current_round >= total_rounds:
        return finish_game(room)

    state["round"] = current_round + 1

    _load_current_round(room)

    state["status"] = "playing"

    room.touch()

    return public_room_state(room)


# ==========================================================
# FINISH GAME
# ==========================================================

def finish_game(room) -> dict[str, Any]:
    """
    Finish the game and determine the winner.
    """

    state = room.state

    state["status"] = "finished"
    state["revealed"] = True
    state["game_finished_at"] = time.time()

    # Sort highest score first.
    players = sorted(
        room.players.values(),
        key=lambda player: (
            room.get_score(player["user_id"]),
            -float(player.get("joined_at", 0)),
        ),
        reverse=True,
    )

    winner = None

    if players:
        top_score = room.get_score(players[0]["user_id"])

        # Tie handling:
        # If multiple players have the same top score,
        # declare a tie rather than arbitrarily selecting one.
        tied = [
            player
            for player in players
            if room.get_score(player["user_id"]) == top_score
        ]

        if len(tied) == 1:
            winner = {
                "name": tied[0].get("name", "Player"),
                "score": top_score,
            }

            room.winner_id = tied[0]["user_id"]

        else:
            winner = {
                "name": "Tie Game",
                "score": top_score,
                "players": [
                    player.get("name", "Player")
                    for player in tied
                ],
            }

            room.winner_id = None

    state["winner"] = winner

    room.finished = True

    room.touch()

    return public_room_state(room)


# ==========================================================
# RESET GAME
# ==========================================================

def reset_game(room) -> dict[str, Any]:
    """
    Reset a Dirty Minds room back to waiting.

    Useful if the host wants to start a completely new game.
    """

    room.state = create_dirty_minds_state()

    room.started = False
    room.finished = False
    room.winner_id = None

    room.reset_scores()

    room.touch()

    return public_room_state(room)


# ==========================================================
# PLAYER-SPECIFIC INFORMATION
# ==========================================================

def _player_submission(
    room,
    player_key: str | None,
) -> dict[str, Any] | None:
    """
    Get the current player's submission.
    """

    if not player_key:
        return None

    return room.state.get("answers", {}).get(player_key)


# ==========================================================
# PUBLIC GAME STATE
# ==========================================================

def public_room_state(
    room,
    player_key: str | None = None,
) -> dict[str, Any]:
    """
    Return information safe to send to a browser.

    IMPORTANT:
    The correct answer is hidden until the round is revealed.
    """

    state = room.state

    status = state.get("status", "waiting")

    revealed = bool(state.get("revealed", False))

    current_answer = ""

    if revealed:
        current_answer = state.get(
            "current_answer",
            "",
        )

    submission = _player_submission(
        room,
        player_key,
    )

    my_submitted = submission is not None

    my_correct = None

    if submission is not None and revealed:
        my_correct = bool(
            submission.get("correct", False)
        )

    # Build player list without exposing:
    #   - Telegram user IDs
    #   - player keys
    #   - internal timestamps
    players = []

    for player in room.players.values():
        players.append(
            {
                "name": player.get(
                    "name",
                    "Player",
                ),
                "score": room.get_score(
                    player.get("user_id")
                ),
                "host": bool(
                    player.get("host", False)
                ),
            }
        )

    result = {
        "room_id": room.room_id,
        "game_id": room.game_id,
        "game_name": room.game_name,

        "status": status,

        "round": int(
            state.get("round", 0)
        ),

        "total_rounds": int(
            state.get(
                "total_rounds",
                TOTAL_ROUNDS,
            )
        ),

        "clue": state.get(
            "current_clue",
            "",
        ),

        # Answer remains hidden until reveal.
        "answer": current_answer,

        "revealed": revealed,

        "player_count": room.player_count(),

        "max_players": room.max_players,

        "min_players": room.min_players,

        "players": players,

        "submitted_count": len(
            state.get("answers", {})
        ),

        "my_submitted": my_submitted,

        "my_correct": my_correct,

        "round_winner": None,

        "round_results": [],

        "winner": state.get("winner"),

        "started": bool(room.started),

        "finished": bool(room.finished),

        "is_host": False,

        "can_start": False,

        "can_reveal": False,

        "can_next": False,
    }

    # ------------------------------------------------------
    # Current player's host status
    # ------------------------------------------------------

    if player_key:
        player = room.get_player_by_key(player_key)

        if player:
            result["is_host"] = bool(
                player.get("host", False)
            )

    # ------------------------------------------------------
    # Host controls
    # ------------------------------------------------------

    result["can_start"] = (
        result["is_host"]
        and status in {"waiting", "finished"}
        and room.player_count() >= room.min_players
    )

    result["can_reveal"] = (
        result["is_host"]
        and status == "playing"
        and not revealed
    )

    result["can_next"] = (
        result["is_host"]
        and status == "revealed"
    )

    # ------------------------------------------------------
    # Reveal information
    # ------------------------------------------------------

    if revealed:
        result["round_winner"] = state.get(
            "round_winner"
        )

        result["round_results"] = list(
            state.get(
                "round_results",
                [],
            )
        )

    return result


# ==========================================================
# UTILITY FUNCTIONS
# ==========================================================

def get_current_clue(room) -> dict[str, Any] | None:
    """
    Return the current clue internally.

    This should NOT be sent directly to the browser because
    it contains the answer.
    """

    state = room.state

    round_number = int(
        state.get("round", 0)
    )

    rounds = state.get("rounds", [])

    if round_number < 1:
        return None

    if round_number > len(rounds):
        return None

    return rounds[round_number - 1]


def get_correct_answer(room) -> str:
    """
    Get the correct answer internally.
    """

    return str(
        room.state.get(
            "current_answer",
            "",
        )
    )


def player_has_submitted(
    room,
    player_key: str,
) -> bool:
    """
    Check whether a player has submitted an answer
    for the current round.
    """

    if not player_key:
        return False

    return player_key in room.state.get(
        "answers",
        {},
    )


def all_players_submitted(room) -> bool:
    """
    Return True when every player has submitted.
    """

    player_count = room.player_count()

    if player_count == 0:
        return False

    submitted_count = len(
        room.state.get(
            "answers",
            {},
        )
    )

    return submitted_count >= player_count
