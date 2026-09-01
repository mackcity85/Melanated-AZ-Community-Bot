# ==========================================================
# Monopoly Web Interface
# ==========================================================

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)

from .game import (
    create_game,
    get_game,
)


monopoly_bp = Blueprint(
    "monopoly",
    __name__,
    url_prefix="/real-games/monopoly",
    template_folder="../templates",
)


@monopoly_bp.get("/")
def monopoly_home():

    return render_template(
        "monopoly.html"
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
        data.get("player_name", "Player")
    ).strip()

    if not player_id:
        return jsonify({
            "error": "Missing player ID."
        }), 400

    game = create_game(
        player_id,
        player_name,
    )

    return jsonify({
        "game_id": game.id,
        "state": game.state(),
    })


@monopoly_bp.post("/<game_id>/join")
def join(game_id):

    game = get_game(game_id)

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
        data.get("player_name", "Player")
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
        game.state()
    )


@monopoly_bp.post("/<game_id>/start")
def start(game_id):

    game = get_game(game_id)

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
        game.state()
    )


@monopoly_bp.post("/<game_id>/roll")
def roll(game_id):

    game = get_game(game_id)

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
        game.state()
    )


@monopoly_bp.post("/<game_id>/buy")
def buy(game_id):

    game = get_game(game_id)

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

        game.buy_property(
            player_id
        )

    except ValueError as exc:

        return jsonify({
            "error": str(exc)
        }), 400

    return jsonify(
        game.state()
    )


@monopoly_bp.get("/<game_id>/state")
def state(game_id):

    game = get_game(game_id)

    if not game:
        return jsonify({
            "error": "Game not found."
        }), 404

    return jsonify(
        game.state()
    )
