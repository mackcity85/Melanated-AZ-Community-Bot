"""
Melanated AZ Bot
Real Games Package
"""

from .routes import real_games_bp
from .deep_links import handle_real_game_deep_link

__all__ = [
    "real_games_bp",
    "handle_real_game_deep_link",
]
