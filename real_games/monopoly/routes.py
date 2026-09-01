"""
Web routes for the Monopoly game.
"""

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)

from ..game_manager import GAME_MANAGER

from .game import MonopolyGame


monopoly_bp = Blueprint(
    "monopoly",
    __name__,
    url_prefix="/real-games/monopoly",
    template_folder="../templates",
)


@monopoly_bp.get("/")
def home():

    return render_template(
        "monopoly.html"
    )


@monopoly_bp.get("/<game_id>")
def room(game_id):

    game = GAME_MANAGER.get(
        game_id.upper()
    )

    if not game:
        return (
            "Game not found.",
            404,
        )

    return render_template(
        "monopoly.html",
        game_id=game.game_id,
    )


@monopoly_bp.post("/create")
def create():

    data = request.get_json(
        silent=True
    ) or {}

    player_id = str(
        data.get("player_id", "")
    ).strip()

    player_name = str(
        data.get(
            "player_name",
            "Player",
        )
    ).strip()

    if not player_id:
        return jsonify({
            "error": "Missing player ID."
        }), 400

    game = MonopolyGame(
        player_id,
        player_name,
    )

    GAME_MANAGER.create(game)

    return jsonify(
        game.serialize()
    )


@monopoly_bp.post("/<game_id>/join")
def join(game_id):

    game = GAME_MANAGER.get(
        game_id.upper()
    )

    if not game:
        return jsonify({
            "error": "Game not found."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    player_id = str(
        data.get("player_id", "")
    ).strip()

    player_name = str(
        data.get(
            "player_name",
            "Player",
        )
    ).strip()

    try:

        game.add_player(
            player_id,
            player_name,
        )

    except ValueError as exc:

        return jsonify({
            "error": str(exc)
        }), 400

    return jsonify(
        game.serialize()
    )


@monopoly_bp.post("/<game_id>/start")
def start(game_id):

    game = GAME_MANAGER.get(
        game_id.upper()
    )

    if not game:
        return jsonify({
            "error": "Game not found."
        }), 404

    try:

        game.start()

    except ValueError as exc:

        return jsonify({
            "error": str(exc)
        }), 400

    return jsonify(
        game.serialize()
    )


@monopoly_bp.post("/<game_id>/roll")
def roll(game_id):

    game = GAME_MANAGER.get(
        game_id.upper()
    )

    if not game:
        return jsonify({
            "error": "Game not found."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    player_id = str(
        data.get("player_id", "")
    ).strip()

    try:

        game.roll(
            player_id
        )

    except ValueError as exc:

        return jsonify({
            "error": str(exc)
        }), 400

    return jsonify(
        game.serialize()
    )


@monopoly_bp.post("/<game_id>/buy")
def buy(game_id):

    game = GAME_MANAGER.get(
        game_id.upper()
    )

    if not game:
        return jsonify({
            "error": "Game not found."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    player_id = str(
        data.get("player_id", "")
    ).strip()

    try:

        game.buy(
            player_id
        )

    except ValueError as exc:

        return jsonify({
            "error": str(exc)
        }), 400

    return jsonify(
        game.serialize()
    )


@monopoly_bp.get("/<game_id>/state")
def state(game_id):

    game = GAME_MANAGER.get(
        game_id.upper()
    )

    if not game:
        return jsonify({
            "error": "Game not found."
        }), 404

    return jsonify(
        game.serialize()
    )
