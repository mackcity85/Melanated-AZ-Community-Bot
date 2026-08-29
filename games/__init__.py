# ==========================================================
# Melanated AZ Bot
# games/__init__.py
#
# Games package
#
# This file makes the games folder a Python package and
# provides a clean central import point for the game system.
# ==========================================================

"""
Melanated AZ Bot Games Package.

All games and game-category functionality should live inside
this package.

The main entry point is games.py.
"""

from .games import (
    games_menu,
    games_callback,
)


__all__ = [
    "games_menu",
    "games_callback",
]
