"""
Melanated AZ Bot
Real Games Package

This package is intentionally separate from the existing
games/ package.
"""

from .routes import real_games_bp
from .deep_links import handle_real_game_deep_link

__all__ = [
    "real_games_bp",
    "handle_real_game_deep_link",
]
