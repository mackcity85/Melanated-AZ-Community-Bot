# ==========================================================
# Melanated AZ Real Games
# real_games.py
#
# PC + MOBILE COMPATIBLE
#
# SINGLE SOURCE OF TRUTH FOR:
# - Real Games registry
# - Flask routes
# - Multiplayer rooms
# - Dirty Minds multiplayer
# ==========================================================

from flask import Blueprint, render_template, jsonify, request
import uuid
import random
import time


# ==========================================================
# BLUEPRINT
# ==========================================================

real_games_bp = Blueprint(
    "real_games",
    __name__,
    url_prefix="/real-games",
    template_folder="templates",
)


# ==========================================================
# GAME REGISTRY
# ==========================================================

GAMES = [

    # ======================================================
    # ARCADE
    # ======================================================

    {
        "game_id": "snake",
        "name": "Snake",
        "icon": "🐍",
        "category": "Arcade",
        "description": (
            "Eat the food, grow longer, "
            "and don't hit yourself."
        ),
    },

    {
        "game_id": "pong",
        "name": "Pong",
        "icon": "🏓",
        "category": "Arcade",
        "description": (
            "Classic paddle battle against "
            "the computer."
        ),
    },

    {
        "game_id": "breakout",
        "name": "Breakout",
        "icon": "🧱",
        "category": "Arcade",
        "description": (
            "Break the blocks and keep "
            "the ball alive."
        ),
    },

    {
        "game_id": "dodge",
        "name": "Dodge",
        "icon": "💥",
        "category": "Arcade",
        "description": (
            "Move around and survive "
            "as long as possible."
        ),
    },

    {
        "game_id": "2048",
        "name": "2048",
        "icon": "🔢",
        "category": "Arcade",
        "description": (
            "Combine matching numbers "
            "and reach 2048."
        ),
    },

    {
        "game_id": "memory_match",
        "name": "Memory Match",
        "icon": "🧠",
        "category": "Arcade",
        "description": (
            "Find every matching pair."
        ),
    },

    {
        "game_id": "reaction",
        "name": "Reaction Test",
        "icon": "⚡",
        "category": "Arcade",
        "description": (
            "Wait for the signal and react "
            "as quickly as possible."
        ),
    },

    {
        "game_id": "whack_a_mole",
        "name": "Whack-a-Mole",
        "icon": "🔨",
        "category": "Arcade",
        "description": (
            "Tap the mole before "
            "it disappears."
        ),
    },


    # ======================================================
    # SPORTS
    # ======================================================

    {
        "game_id": "basketball",
        "name": "Basketball",
        "icon": "🏀",
        "category": "Sports",
        "description": (
            "Shoot the ball and score "
            "as many baskets as possible."
        ),
    },


    # ======================================================
    # SHOOTING
    # ======================================================

    {
        "game_id": "target_shooter",
        "name": "Target Shooter",
        "icon": "🎯",
        "category": "Shooting",
        "description": (
            "Hit as many targets as possible "
            "before time runs out."
        ),
    },


    # ======================================================
    # BOARD GAMES
    # ======================================================

    {
        "game_id": "chess",
        "name": "Chess",
        "icon": "♟️",
        "category": "Board Games",
        "description": (
            "Classic two-player chess."
        ),
    },

    {
        "game_id": "checkers",
        "name": "Checkers",
        "icon": "🔴",
        "category": "Board Games",
        "description": (
            "Jump, capture, king your pieces, "
            "and defeat your opponent."
        ),
    },

    {
        "game_id": "monopoly",
        "name": "Monopoly",
        "icon": "🎲",
        "category": "Board Games",
        "description": (
            "Buy properties, collect rent, "
            "and build your fortune."
        ),
    },


    # ======================================================
    # PARTY / TRIVIA
    # ======================================================

    {
        "game_id": "dirty_minds",
        "name": "Dirty Minds",
        "icon": "🧠",
        "category": "Party",
        "description": (
            "Multiplayer dirty-minded guessing game. "
            "The clues sound naughty, but the answers are innocent."
        ),
    },


    # ======================================================
    # RACING
    # ======================================================

    {
        "game_id": "race_car",
        "name": "Race Car Racing",
        "icon": "🏎️",
        "category": "Racing",
        "description": (
            "Dodge traffic, increase your speed, "
            "and see how far you can race."
        ),
    },
]


# ==========================================================
# VALID GAME IDS
# ==========================================================

VALID_GAME_IDS = {
    game["game_id"]
    for game in GAMES
}


# ==========================================================
# ROOM STORAGE
# ==========================================================
#
# Existing lightweight room system.
#
# Dirty Minds uses this dictionary directly so Telegram
# and browser requests can operate on the same room state
# when running inside the same Render process.
#
# For multiple Render instances, move this to Redis later.
# ==========================================================

rooms = {}


# ==========================================================
# DIRTY MINDS QUESTIONS
# ==========================================================
#
# These are ORIGINAL questions.
#
# They are not copied from the commercial Dirty Minds game.
# ==========================================================

DIRTY_MINDS_QUESTIONS = [

    {
        "clue": "I'm long, hard, and people hold me when they write.",
        "answer": "A pencil",
    },

    {
        "clue": "You put me in your mouth every morning and move me around.",
        "answer": "A toothbrush",
    },

    {
        "clue": "The more you rub me, the smaller I become.",
        "answer": "An eraser",
    },

    {
        "clue": "I'm hot, steamy, and usually happen in the bathroom.",
        "answer": "A shower",
    },

    {
        "clue": "You blow me up before a party.",
        "answer": "A balloon",
    },

    {
        "clue": "You pull me out before you sit down.",
        "answer": "A chair",
    },

    {
        "clue": "I'm worn in pairs and go on your feet.",
        "answer": "Socks",
    },

    {
        "clue": "You can squeeze me, and I clean up a mess.",
        "answer": "A sponge",
    },

    {
        "clue": "I have a head and a tail but no body.",
        "answer": "A coin",
    },

    {
        "clue": "You can open me, close me, and look through me.",
        "answer": "A window",
    },

    {
        "clue": "I'm stiff when cold and soft when warm.",
        "answer": "Butter",
    },

    {
        "clue": "You can slide me into a slot to pay for something.",
        "answer": "A card",
    },

    {
        "clue": "I have teeth but I never bite.",
        "answer": "A comb",
    },

    {
        "clue": "You hold me by the handle and use me to sweep.",
        "answer": "A broom",
    },

    {
        "clue": "You can shake me, and I make noise at a party.",
        "answer": "A maraca",
    },

    {
        "clue": "You can peel me, but I'm not wearing clothes.",
        "answer": "A banana",
    },

    {
        "clue": "You stick me on an envelope before you send it.",
        "answer": "A stamp",
    },

    {
        "clue": "I'm something you can wear around your neck.",
        "answer": "A necklace",
    },

    {
        "clue": "You turn me on when the room gets dark.",
        "answer": "A light",
    },

    {
        "clue": "You can whip me, but I'm usually found in a kitchen.",
        "answer": "Cream",
    },

    {
        "clue": "You can spread me on bread.",
        "answer": "Peanut butter",
    },

    {
        "clue": "I'm round, you can bounce me, and I belong on a court.",
        "answer": "A basketball",
    },

    {
        "clue": "You can sit on me, but you can also fold me up.",
        "answer": "A chair",
    },

    {
        "clue": "I have a handle and bristles and help clean your teeth.",
        "answer": "A toothbrush",
    },

]


# ==========================================================
# GAME HELPERS
# ==========================================================

def get_game(game_id):
    """
    Return a game from the registry.
    """

    if not game_id:
        return None

    game_id = str(game_id).strip().lower()

    for game in GAMES:

        if game["game_id"].lower() == game_id:
            return game

    return None


def games_by_category():
    """
    Group games by category.
    """

    categories = {}

    for game in GAMES:

        category = game["category"]

        if category not in categories:
            categories[category] = []

        categories[category].append(game)

    return categories


# ==========================================================
# ROOM HELPERS
# ==========================================================

def create_room_data(game_id, host_id=None, host_name=None):

    room_id = uuid.uuid4().hex[:8].upper()

    room = {
        "room_id": room_id,
        "game_id": game_id,
        "game_name": get_game(game_id)["name"],
        "host_id": str(host_id) if host_id else None,
        "players": {},
        "created_at": time.time(),
        "started": False,
        "finished": False,
    }

    if host_id:

        room["players"][str(host_id)] = {
            "player_id": str(host_id),
            "name": host_name or "Host",
            "score": 0,
            "joined_at": time.time(),
            "connected": True,
        }

    return room


def get_room(room_id):

    if not room_id:
        return None

    return rooms.get(
        str(room_id).strip().upper()
    )


def dirty_room_public(room):

    if not room:
        return None

    players = []

    for player in room["players"].values():

        players.append(
            {
                "player_id": player["player_id"],
                "name": player["name"],
                "score": player["score"],
                "connected": player.get(
                    "connected",
                    True
                ),
            }
        )

    players.sort(
        key=lambda p: (
            -p["score"],
            p["name"].lower()
        )
    )

    public = {
        "room_id": room["room_id"],
        "game_id": room["game_id"],
        "game_name": room["game_name"],
        "host_id": room["host_id"],
        "started": room["started"],
        "finished": room["finished"],
        "players": players,
    }

    if room["game_id"] == "dirty_minds":

        public.update(
            {
                "round": room.get("round", 0),
                "total_rounds": room.get(
                    "total_rounds",
                    10
                ),
                "phase": room.get(
                    "phase",
                    "lobby"
                ),
                "question": room.get(
                    "question"
                ),
                "answer": (
                    room.get("answer")
                    if room.get("phase") == "reveal"
                    else None
                ),
                "answers": (
                    room.get("answers", {})
                    if room.get("phase") == "reveal"
                    else {}
                ),
                "winner": room.get("winner"),
            }
        )

    return public


# ==========================================================
# DIRTY MINDS ROOM INITIALIZATION
# ==========================================================

def initialize_dirty_minds(room):

    questions = DIRTY_MINDS_QUESTIONS[:]

    random.shuffle(questions)

    total_rounds = min(
        10,
        len(questions)
    )

    room.update(
        {
            "started": False,
            "finished": False,
            "round": 0,
            "total_rounds": total_rounds,
            "questions": questions[:total_rounds],
            "phase": "lobby",
            "question": None,
            "answer": None,
            "answers": {},
            "winner": None,
        }
    )


# ==========================================================
# REAL GAMES HOME
# ==========================================================

@real_games_bp.route("/")
def real_games_home():

    return render_template(
        "real_games.html",
        games=GAMES,
        categories=games_by_category(),
    )


# ==========================================================
# PLAY GAME
# ==========================================================

@real_games_bp.route("/play/<game_id>")
def play_game(game_id):

    game = get_game(game_id)

    if game is None:

        return (
            render_template(
                "game.html",
                game={
                    "game_id": "unknown",
                    "name": "Game Not Found",
                    "icon": "❌",
                    "category": "Unknown",
                    "description": (
                        "This game is not available."
                    ),
                },
            ),
            404,
        )

    return render_template(
        "game.html",
        game=game,
    )


# ==========================================================
# GAME API
# ==========================================================

@real_games_bp.route("/api/games")
def api_games():

    return jsonify(
        {
            "success": True,
            "count": len(GAMES),
            "games": GAMES,
            "categories": games_by_category(),
        }
    )


# ==========================================================
# CREATE ROOM
# ==========================================================

@real_games_bp.route(
    "/create-room",
    methods=["POST"]
)
def create_room():

    data = request.get_json(
        silent=True
    ) or {}

    game_id = str(
        data.get(
            "game_id",
            ""
        )
    ).strip().lower()

    game = get_game(game_id)

    if game is None:

        return jsonify(
            {
                "success": False,
                "error": "Game not found",
            }
        ), 404

    player_id = data.get(
        "player_id"
    )

    player_name = data.get(
        "player_name"
    ) or "Player"

    room = create_room_data(
        game_id,
        player_id,
        player_name,
    )

    rooms[room["room_id"]] = room

    if game_id == "dirty_minds":

        initialize_dirty_minds(
            room
        )

    return jsonify(
        {
            "success": True,
            "room_id": room["room_id"],
            "game_id": game_id,
            "game": game,
            "room": dirty_room_public(room),
        }
    )


# ==========================================================
# ROOM INFO
# ==========================================================

@real_games_bp.route(
    "/room/<room_id>"
)
def room_info(room_id):

    room = get_room(room_id)

    if room is None:

        return jsonify(
            {
                "success": False,
                "error": "Room not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "room": dirty_room_public(room),
        }
    )


# ==========================================================
# JOIN ROOM
# ==========================================================

@real_games_bp.route(
    "/room/<room_id>/join",
    methods=["POST"]
)
def join_room(room_id):

    room = get_room(room_id)

    if room is None:

        return jsonify(
            {
                "success": False,
                "error": "Room not found",
            }
        ), 404

    data = request.get_json(
        silent=True
    ) or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    ).strip()

    player_name = str(
        data.get(
            "player_name",
            "Player"
        )
    ).strip()

    if not player_id:

        return jsonify(
            {
                "success": False,
                "error": "Player ID is required.",
            }
        ), 400

    if not player_name:

        player_name = "Player"

    # ------------------------------------------------------
    # Existing player reconnect
    # ------------------------------------------------------

    if player_id in room["players"]:

        room["players"][player_id][
            "name"
        ] = player_name

        room["players"][player_id][
            "connected"
        ] = True

        return jsonify(
            {
                "success": True,
                "room": dirty_room_public(room),
            }
        )

    # ------------------------------------------------------
    # Do not allow joining a finished game
    # ------------------------------------------------------

    if room.get("finished"):

        return jsonify(
            {
                "success": False,
                "error": "This game has already ended.",
            }
        ), 400

    # ------------------------------------------------------
    # Dirty Minds player limit
    # ------------------------------------------------------

    if room["game_id"] == "dirty_minds":

        if len(room["players"]) >= 20:

            return jsonify(
                {
                    "success": False,
                    "error": (
                        "This Dirty Minds room "
                        "is full. Maximum 20 players."
                    ),
                }
            ), 400

    room["players"][player_id] = {
        "player_id": player_id,
        "name": player_name[:40],
        "score": 0,
        "joined_at": time.time(),
        "connected": True,
    }

    return jsonify(
        {
            "success": True,
            "room": dirty_room_public(room),
        }
    )


# ==========================================================
# DIRTY MINDS — START
# ==========================================================

@real_games_bp.route(
    "/room/<room_id>/dirty-minds/start",
    methods=["POST"]
)
def dirty_minds_start(room_id):

    room = get_room(room_id)

    if room is None:

        return jsonify(
            {
                "success": False,
                "error": "Room not found",
            }
        ), 404

    if room["game_id"] != "dirty_minds":

        return jsonify(
            {
                "success": False,
                "error": "This is not a Dirty Minds room.",
            }
        ), 400

    data = request.get_json(
        silent=True
    ) or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    )

    if player_id != str(
        room.get("host_id")
    ):

        return jsonify(
            {
                "success": False,
                "error": "Only the host can start the game.",
            }
        ), 403

    if len(room["players"]) < 2:

        return jsonify(
            {
                "success": False,
                "error": (
                    "At least 2 players are "
                    "needed to start Dirty Minds."
                ),
            }
        ), 400

    room["started"] = True
    room["finished"] = False
    room["round"] = 1
    room["phase"] = "question"

    room["question"] = room[
        "questions"
    ][0]["clue"]

    room["answer"] = room[
        "questions"
    ][0]["answer"]

    room["answers"] = {}

    return jsonify(
        {
            "success": True,
            "room": dirty_room_public(room),
        }
    )


# ==========================================================
# DIRTY MINDS — SUBMIT ANSWER
# ==========================================================

@real_games_bp.route(
    "/room/<room_id>/dirty-minds/answer",
    methods=["POST"]
)
def dirty_minds_answer(room_id):

    room = get_room(room_id)

    if room is None:

        return jsonify(
            {
                "success": False,
                "error": "Room not found.",
            }
        ), 404

    if room["game_id"] != "dirty_minds":

        return jsonify(
            {
                "success": False,
                "error": "This is not a Dirty Minds room.",
            }
        ), 400

    if room.get("phase") != "question":

        return jsonify(
            {
                "success": False,
                "error": "Answers are not being accepted right now.",
            }
        ), 400

    data = request.get_json(
        silent=True
    ) or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    ).strip()

    answer = str(
        data.get(
            "answer",
            ""
        )
    ).strip()

    if player_id not in room["players"]:

        return jsonify(
            {
                "success": False,
                "error": "You are not in this room.",
            }
        ), 403

    if not answer:

        return jsonify(
            {
                "success": False,
                "error": "Enter an answer first.",
            }
        ), 400

    if len(answer) > 200:

        answer = answer[:200]

    room["answers"][player_id] = answer

    # ------------------------------------------------------
    # Automatically reveal once everyone has answered.
    # ------------------------------------------------------

    active_players = [
        pid
        for pid in room["players"]
    ]

    all_answered = all(
        pid in room["answers"]
        for pid in active_players
    )

    if all_answered:

        room["phase"] = "reveal"

        # Award one point for submitting an answer.
        # Additional host scoring can happen on reveal.
        for pid in active_players:

            if pid in room["players"]:
                room["players"][pid][
                    "score"
                ] += 1

    return jsonify(
        {
            "success": True,
            "all_answered": all_answered,
            "room": dirty_room_public(room),
        }
    )


# ==========================================================
# DIRTY MINDS — REVEAL
# ==========================================================

@real_games_bp.route(
    "/room/<room_id>/dirty-minds/reveal",
    methods=["POST"]
)
def dirty_minds_reveal(room_id):

    room = get_room(room_id)

    if room is None:

        return jsonify(
            {
                "success": False,
                "error": "Room not found.",
            }
        ), 404

    if room["game_id"] != "dirty_minds":

        return jsonify(
            {
                "success": False,
                "error": "This is not a Dirty Minds room.",
            }
        ), 400

    data = request.get_json(
        silent=True
    ) or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    )

    if player_id != str(
        room.get("host_id")
    ):

        return jsonify(
            {
                "success": False,
                "error": "Only the host can reveal.",
            }
        ), 403

    room["phase"] = "reveal"

    return jsonify(
        {
            "success": True,
            "room": dirty_room_public(room),
        }
    )


# ==========================================================
# DIRTY MINDS — NEXT ROUND
# ==========================================================

@real_games_bp.route(
    "/room/<room_id>/dirty-minds/next",
    methods=["POST"]
)
def dirty_minds_next(room_id):

    room = get_room(room_id)

    if room is None:

        return jsonify(
            {
                "success": False,
                "error": "Room not found.",
            }
        ), 404

    if room["game_id"] != "dirty_minds":

        return jsonify(
            {
                "success": False,
                "error": "This is not a Dirty Minds room.",
            }
        ), 400

    data = request.get_json(
        silent=True
    ) or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    )

    if player_id != str(
        room.get("host_id")
    ):

        return jsonify(
            {
                "success": False,
                "error": "Only the host can advance the game.",
            }
        ), 403

    current_round = int(
        room.get("round", 0)
    )

    total_rounds = int(
        room.get(
            "total_rounds",
            10
        )
    )

    # ------------------------------------------------------
    # GAME OVER
    # ------------------------------------------------------

    if current_round >= total_rounds:

        room["finished"] = True
        room["started"] = False
        room["phase"] = "finished"

        ranked = sorted(
            room["players"].values(),
            key=lambda p: p["score"],
            reverse=True,
        )

        if ranked:

            room["winner"] = {
                "player_id": ranked[0][
                    "player_id"
                ],
                "name": ranked[0]["name"],
                "score": ranked[0]["score"],
            }

        return jsonify(
            {
                "success": True,
                "room": dirty_room_public(room),
            }
        )

    # ------------------------------------------------------
    # NEXT QUESTION
    # ------------------------------------------------------

    room["round"] = current_round + 1

    question_index = (
        room["round"] - 1
    )

    question = room[
        "questions"
    ][question_index]

    room["question"] = question[
        "clue"
    ]

    room["answer"] = question[
        "answer"
    ]

    room["answers"] = {}

    room["phase"] = "question"

    return jsonify(
        {
            "success": True,
            "room": dirty_room_public(room),
        }
    )


# ==========================================================
# LEAVE / DISCONNECT
# ==========================================================

@real_games_bp.route(
    "/room/<room_id>/leave",
    methods=["POST"]
)
def leave_room(room_id):

    room = get_room(room_id)

    if room is None:

        return jsonify(
            {
                "success": False,
                "error": "Room not found.",
            }
        ), 404

    data = request.get_json(
        silent=True
    ) or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    ).strip()

    if player_id in room["players"]:

        room["players"][
            player_id
        ]["connected"] = False

    return jsonify(
        {
            "success": True,
            "room": dirty_room_public(room),
        }
    )


# ==========================================================
# HEALTH / STATUS
# ==========================================================

@real_games_bp.route(
    "/api/status"
)
def api_status():

    return jsonify(
        {
            "success": True,
            "service": "Melanated AZ Real Games",
            "status": "online",
            "games": len(GAMES),
            "game_ids": sorted(
                VALID_GAME_IDS
            ),
            "rooms": len(rooms),
        }
    )


# ==========================================================
# EXPORTS
# ==========================================================

__all__ = [
    "real_games_bp",
    "GAMES",
    "VALID_GAME_IDS",
    "rooms",
    "get_game",
    "games_by_category",
    "DIRTY_MINDS_QUESTIONS",
]
