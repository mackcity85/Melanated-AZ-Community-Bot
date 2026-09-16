# ==========================================================
# Melanated AZ Bot - Retro Console Game Center Catalog
# ==========================================================
# Console families only. Playable games will be added one
# console/system at a time. No placeholder games are exposed.
# ==========================================================

CONSOLES = {
    "nintendo": {
        "title": "🟥 NINTENDO",
        "systems": [
            ("nes", "NES"),
            ("snes", "SNES"),
            ("gameboy", "Game Boy"),
            ("gbc", "Game Boy Color"),
            ("n64", "Nintendo 64"),
            ("gba", "Game Boy Advance"),
            ("gamecube", "GameCube"),
        ],
    },
    "sega": {
        "title": "🔵 SEGA",
        "systems": [
            ("mastersystem", "Master System"),
            ("genesis", "Genesis / Mega Drive"),
            ("gamegear", "Game Gear"),
            ("saturn", "Saturn"),
            ("dreamcast", "Dreamcast"),
        ],
    },
    "playstation": {
        "title": "🟦 PLAYSTATION",
        "systems": [
            ("ps1", "PlayStation"),
            ("ps2", "PlayStation 2"),
            ("psp", "PSP"),
            ("ps3", "PlayStation 3"),
        ],
    },
    "xbox": {
        "title": "🟩 XBOX",
        "systems": [
            ("xbox", "Original Xbox"),
            ("xbox360", "Xbox 360"),
            ("xboxone", "Xbox One"),
        ],
    },
}

CONSOLE_ORDER = ["nintendo", "sega", "playstation", "xbox"]

CONSOLE_BUTTONS = {
    "nintendo": "🟥 Nintendo",
    "sega": "🔵 Sega",
    "playstation": "🟦 PlayStation",
    "xbox": "🟩 Xbox",
}


def get_console(console_id):
    return CONSOLES.get(console_id)


def get_system(console_id, system_id):
    console = get_console(console_id)
    if not console:
        return None
    for item_id, name in console["systems"]:
        if item_id == system_id:
            return {"id": item_id, "name": name}
    return None
