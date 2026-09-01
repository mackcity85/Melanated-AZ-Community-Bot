"""
Real Games main web routes.
"""

from flask import (
    Blueprint,
    render_template,
)


real_games_bp = Blueprint(
    "real_games",
    __name__,
    url_prefix="/real-games",
    template_folder="templates",
)


@real_games_bp.get("/")
def real_games_home():

    return render_template(
        "real_games.html"
    )
