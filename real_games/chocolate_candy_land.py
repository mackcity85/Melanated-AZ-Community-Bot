"""Dedicated browser route for Chocolate Candy Land."""
from .real_games import real_games_bp


@real_games_bp.route("/play/chocolate_candy_land")
def chocolate_candy_land_page():
    return __import__("flask").render_template("chocolate_candy_land.html")
