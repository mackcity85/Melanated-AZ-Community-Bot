from __future__ import annotations

# Original browser games for every remaining console/system in the catalog.
# These are console-era-inspired games, not ROMs or ports.

SYSTEMS = {
    "gameboy": ("Game Boy", [("Pocket Runner", "🏃"), ("Dot Defender", "🛡️"), ("Pocket Racer", "🏎️")]),
    "gbc": ("Game Boy Color", [("Color Clash", "🎨"), ("Color Defender", "🚀"), ("Color Racer", "🏁")]),
    "n64": ("Nintendo 64", [("64 Turbo Circuit", "🏎️"), ("64 Star Battle", "⭐"), ("64 Sky Jump", "🦘")]),
    "gba": ("Game Boy Advance", [("Advance Rush", "⚡"), ("Advance Blaster", "🔫"), ("Advance Rally", "🏁")]),
    "gamecube": ("GameCube", [("Cube Kart", "🏎️"), ("Cube Combat", "🥊"), ("Cube Quest", "🗺️")]),
    "mastersystem": ("Master System", [("Master Dash", "🏃"), ("Master Blaster", "🚀"), ("Master Rally", "🏎️")]),
    "genesis": ("Genesis / Mega Drive", [("Genesis Street Racer", "🏎️"), ("Genesis Strike", "💥"), ("Genesis Galaxy", "🌌")]),
    "gamegear": ("Game Gear", [("Gear Rush", "🏃"), ("Gear Blaster", "🔫"), ("Gear Drift", "🏎️")]),
    "saturn": ("Saturn", [("Saturn Circuit", "🏎️"), ("Saturn Assault", "🚀"), ("Saturn Arena", "⚔️")]),
    "dreamcast": ("Dreamcast", [("Dream Sprint", "🏃"), ("Dream Blaster", "🔫"), ("Dream Circuit", "🏎️")]),
    "ps1": ("PlayStation", [("Pixel Pursuit", "🏃"), ("Neon Strike", "🔫"), ("Ridge Rush", "🏎️")]),
    "ps2": ("PlayStation 2", [("Shadow Circuit", "🏎️"), ("Power Arena", "⚔️"), ("Street Rush", "🏃")]),
    "psp": ("PSP", [("Pocket Strike", "🔫"), ("Pocket Drift", "🏎️"), ("Pocket Arena", "⚔️")]),
    "ps3": ("PlayStation 3", [("Neon Velocity", "🏎️"), ("Steel Defender", "🛡️"), ("Galaxy Raid", "🚀")]),
    "xbox": ("Original Xbox", [("Xbox Circuit", "🏎️"), ("Xbox Assault", "🔫"), ("Xbox Arena", "⚔️")]),
    "xbox360": ("Xbox 360", [("360 Velocity", "🏎️"), ("360 Defender", "🚀"), ("360 Street Run", "🏃")]),
    "xboxone": ("Xbox One", [("One Turbo", "🏎️"), ("One Strike", "🔫"), ("One Survival", "🛡️")]),
}


def get_retro_games(system_id: str):
    system = SYSTEMS.get(system_id)
    if not system:
        return []
    title, games = system
    result = []
    modes = ("runner", "shooter", "racer")
    for index, (name, icon) in enumerate(games):
        result.append({
            "game_id": f"retro_{system_id}_{index + 1}",
            "name": name,
            "icon": icon,
            "category": title,
            "description": f"Original {title}-era arcade gameplay: {name}.",
            "system_id": system_id,
            "system_name": title,
            "mode": modes[index],
        })
    return result


def get_all_retro_games():
    games = []
    for system_id in SYSTEMS:
        games.extend(get_retro_games(system_id))
    return games
