# ==========================================================
# Melanated AZ Real Games
# real_games/__init__.py
# ==========================================================

from .real_games import real_games_bp

from .deep_links import (
    real_games_start,
    handle_game_launch,
    handle_dirty_minds_join,
    handle_real_game_deep_link,
    make_web_game_url,
    make_dirty_minds_url,
    get_real_games_handler,
)

__all__ = [
    "real_games_bp",
    "real_games_start",
    "handle_game_launch",
    "handle_dirty_minds_join",
    "handle_real_game_deep_link",
    "make_web_game_url",
    "make_dirty_minds_url",
    "get_real_games_handler",
]
