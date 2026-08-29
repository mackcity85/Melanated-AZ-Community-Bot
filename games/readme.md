==========================================================
MELANATED AZ BOT
GAMES PACKAGE
==========================================================

MAIN ENTRY:
    games.py

GAME DATA:
    game_data.py

CATEGORIES:
    Board & Classic
    Sports
    Arcade & Shooting
    Adventure & Outdoors
    Trivia & Knowledge
    Party & Social
    Spicy / Adult


==========================================================
IMPORTANT
==========================================================

The Admin Panel should have ONE Games button:

    🎮 Games

The Games button should use:

    callback_data="admin_games"

The admin callback router should then open:

    games_menu()


==========================================================
GAME TYPES
==========================================================

monopoly
duck_hunt
fishing
trivia
would_you_rather
truth_dare
sports
arcade
questions
word
board
dice
coin
etc.


==========================================================
ADDING A GAME
==========================================================

Most games only require adding a definition to:

    game_data.py

Example:

    "new_game": {
        "name": "🎮 New Game",
        "category": "arcade",
        "description": "My new game.",
        "type": "arcade",
    }


The main menu automatically discovers it.

==========================================================
