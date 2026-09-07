"""
Melanated AZ Real Games
"""

from .real_games import real_games_bp

try:
    from .deep_links import handle_real_game_deep_link
except ImportError:
    handle_real_game_deep_link = None

__all__ = [
    "real_games_bp",
    "handle_real_game_deep_link",
]
