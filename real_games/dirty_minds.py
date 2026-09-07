"""
Melanated AZ Real Games
Dirty Minds Multiplayer Engine
"""

from __future__ import annotations

import random
import time


DIRTY_MINDS_CLUES = [
    {
        "clue": "You put it in your mouth, pull it out, and it comes back wet.",
        "answer": "Toothbrush",
    },
    {
        "clue": "The harder you push it, the deeper it goes.",
        "answer": "A button",
    },
    {
        "clue": "It gets longer when you pull it.",
        "answer": "A rubber band",
    },
    {
        "clue": "You can ride it, but you don't need a saddle.",
        "answer": "A bicycle",
    },
    {
        "clue": "You blow it before you put it in.",
        "answer": "A balloon",
    },
    {
        "clue": "It can be hard or soft, and you sleep on it every night.",
        "answer": "A pillow",
    },
    {
        "clue": "You grab it when you need to go faster.",
        "answer": "A steering wheel",
    },
    {
        "clue": "You put it between your legs when you ride.",
        "answer": "A bicycle",
    },
    {
        "clue": "It goes in dry and comes out wet.",
        "answer": "A tea bag",
    },
    {
        "clue": "You lick it before sticking it somewhere.",
        "answer": "A stamp",
    },
    {
        "clue": "You can make it stand up with one hand.",
        "answer": "A deck of cards",
    },
    {
        "clue": "It gets hot when you rub it.",
        "answer": "Your hands",
    },
    {
        "clue": "You put your fingers in it to make it work.",
        "answer": "A glove",
    },
    {
        "clue": "It has a head and a shaft but isn't a person.",
        "answer": "A golf club",
    },
    {
        "clue": "You push it in and pull it out all day.",
        "answer": "A drawer",
    },
    {
        "clue": "It gets wetter the more it dries.",
        "answer": "A towel",
    },
    {
        "clue": "You sit on it, but it can also be opened.",
        "answer": "A toilet",
    },
    {
        "clue": "You put it on your finger before you use it.",
        "answer": "A ring",
    },
    {
        "clue": "It has two balls but isn't a sport.",
        "answer": "A snowman",
    },
    {
        "clue": "You pull it before you push it.",
        "answer": "A door handle",
    },
]


def normalize_answer(value: str) -> str:
    value = (value or "").strip().lower()

    chars = []

    for char in value:
        if char.isalnum() or char.isspace():
            chars.append(char)

    return " ".join("".join(chars).split())


def create_dirty_minds_state():
    clue = random.choice(DIRTY_MINDS_CLUES)

    return {
        "round": 1,
        "status": "waiting",
        "clue": clue["clue"],
        "answer": clue["answer"],
        "answers": {},
        "revealed": False,
        "round_started_at": None,
        "round_seconds": 45,
        "history": [],
    }


def start_game(room):
    if room.game_id != "dirty_minds":
        raise ValueError("This is not a Dirty Minds room.")

    if room.started:
        return

    if len(room.players) < 2:
        raise ValueError(
            "Dirty Minds needs at least 2 players to start."
        )

    room.state = create_dirty_minds_state()

    room.state["status"] = "playing"
    room.state["round_started_at"] = time.time()

    room.started = True
    room.touch()


def submit_answer(room, player_key, answer):
    if room.game_id != "dirty_minds":
        raise ValueError("This is not a Dirty Minds room.")

    player = room.get_player_by_key(player_key)

    if not player:
        raise ValueError("Player is not registered in this room.")

    state = room.state

    if not room.started:
        raise ValueError("The game has not started yet.")

    if state.get("revealed"):
        raise ValueError("This round has already been revealed.")

    answer = (answer or "").strip()

    if not answer:
        raise ValueError("Please enter an answer.")

    state.setdefault("answers", {})[player["user_id"]] = answer

    room.touch()

    return True


def reveal_round(room):
    if room.game_id != "dirty_minds":
        raise ValueError("This is not a Dirty Minds room.")

    state = room.state

    if state.get("revealed"):
        return

    correct_answer = normalize_answer(
        state.get("answer", "")
    )

    answers = state.get("answers", {})

    winners = []

    for user_id, submitted in answers.items():

        if normalize_answer(submitted) == correct_answer:

            player = room.players.get(user_id)

            if player:
                player["score"] = player.get("score", 0) + 1
                winners.append(user_id)

    state["revealed"] = True
    state["status"] = "revealed"
    state["winners"] = winners

    state.setdefault("history", []).append(
        {
            "round": state.get("round", 1),
            "clue": state.get("clue", ""),
            "answer": state.get("answer", ""),
            "answers": dict(answers),
            "winners": list(winners),
        }
    )

    room.touch()


def next_round(room):

    if room.game_id != "dirty_minds":
        raise ValueError("This is not a Dirty Minds room.")

    previous_answer = room.state.get("answer")

    available = [
        clue
        for clue in DIRTY_MINDS_CLUES
        if clue["answer"] != previous_answer
    ]

    clue = random.choice(
        available or DIRTY_MINDS_CLUES
    )

    current_round = int(
        room.state.get("round", 1)
    ) + 1

    room.state = {
        "round": current_round,
        "status": "playing",
        "clue": clue["clue"],
        "answer": clue["answer"],
        "answers": {},
        "revealed": False,
        "round_started_at": time.time(),
        "round_seconds": 45,
        "history": room.state.get("history", []),
    }

    room.touch()


def public_room_state(room):

    state = room.state or {}

    players = []

    for player in room.players.values():

        players.append(
            {
                "user_id": player["user_id"],
                "name": player["name"],
                "score": player.get("score", 0),
                "is_host": player["user_id"] == room.host_id,
                "answered": player["user_id"]
                in state.get("answers", {}),
            }
        )

    players.sort(
        key=lambda item: (
            not item["is_host"],
            item["name"].lower(),
        )
    )

    result = {
        "room_id": room.room_id,
        "game_id": room.game_id,
        "game_name": room.game_name,
        "started": room.started,
        "finished": room.finished,
        "host_id": room.host_id,
        "player_count": len(players),
        "max_players": room.max_players,
        "players": players,
        "state": {
            "round": state.get("round", 1),
            "status": state.get("status", "waiting"),
            "clue": state.get("clue", ""),
            "revealed": state.get("revealed", False),
            "answer": (
                state.get("answer", "")
                if state.get("revealed")
                else None
            ),
            "winners": state.get("winners", []),
            "answered_count": len(
                state.get("answers", {})
            ),
        },
    }

    return result
