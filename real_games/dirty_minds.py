# ==========================================================
# Melanated AZ Real Games
# dirty_minds.py
#
# Multiplayer Dirty Minds game engine.
#
# Features:
#   - Multiplayer rooms
#   - 150 clean-answer clues
#   - 10 random rounds per game
#   - Synchronized rounds
#   - Server-side answer validation
#   - Score tracking
#   - Host controls
#   - Reveal answers
#   - Next-round controls
#   - Safe public game state
#
# IMPORTANT:
# Answers are NEVER exposed to the browser until reveal.
# ==========================================================

from __future__ import annotations

import random
import re
import time
from typing import Any


# ==========================================================
# GAME SETTINGS
# ==========================================================

TOTAL_ROUNDS = 10
POINTS_PER_CORRECT_ANSWER = 1


# ==========================================================
# DIRTY MINDS CLUE BANK
#
# 150 original-style clues.
#
# The clues are intentionally suggestive/misleading while
# the actual answers are ordinary, clean objects or actions.
# ==========================================================

DIRTY_MINDS_CLUES: list[dict[str, Any]] = [

    # ======================================================
    # 1-25
    # ======================================================

    {
        "clue": "You put it in your mouth, pull it out, and it comes back wet.",
        "answer": "toothbrush",
        "aliases": ["tooth brush"],
    },
    {
        "clue": "The harder you push it, the deeper it goes.",
        "answer": "button",
        "aliases": ["a button", "the button"],
    },
    {
        "clue": "It gets longer when you pull it.",
        "answer": "rubber band",
        "aliases": ["rubberband"],
    },
    {
        "clue": "You can ride it, but you don't need a saddle.",
        "answer": "bicycle",
        "aliases": ["bike"],
    },
    {
        "clue": "You blow it before you put it in.",
        "answer": "balloon",
        "aliases": ["a balloon"],
    },
    {
        "clue": "It can be hard or soft, and you sleep on it every night.",
        "answer": "pillow",
        "aliases": ["a pillow"],
    },
    {
        "clue": "You grab it when you need to change direction.",
        "answer": "steering wheel",
        "aliases": ["steeringwheel"],
    },
    {
        "clue": "It goes in dry and comes out wet.",
        "answer": "tea bag",
        "aliases": ["teabag"],
    },
    {
        "clue": "You lick it before sticking it somewhere.",
        "answer": "stamp",
        "aliases": ["a stamp"],
    },
    {
        "clue": "It gets hot when you rub it.",
        "answer": "your hands",
        "aliases": ["hands", "my hands", "your hand"],
    },
    {
        "clue": "You put your fingers in it to make it work.",
        "answer": "glove",
        "aliases": ["a glove"],
    },
    {
        "clue": "It has a head and a shaft but isn't a person.",
        "answer": "golf club",
        "aliases": ["golfclub", "club"],
    },
    {
        "clue": "You push it in and pull it out all day.",
        "answer": "drawer",
        "aliases": ["a drawer"],
    },
    {
        "clue": "It gets wetter the more it dries.",
        "answer": "towel",
        "aliases": ["a towel"],
    },
    {
        "clue": "You sit on it, but it can also be opened.",
        "answer": "toilet",
        "aliases": ["a toilet"],
    },
    {
        "clue": "You put it on your finger before you use it.",
        "answer": "ring",
        "aliases": ["a ring"],
    },
    {
        "clue": "It has two balls but isn't a sport.",
        "answer": "snowman",
        "aliases": ["a snowman"],
    },
    {
        "clue": "You pull it before you push it.",
        "answer": "door handle",
        "aliases": ["doorhandle", "handle"],
    },
    {
        "clue": "You stick it in a hole to open something.",
        "answer": "key",
        "aliases": ["a key"],
    },
    {
        "clue": "You put it in your ear when you want to listen.",
        "answer": "earbud",
        "aliases": ["ear bud", "earphone", "earphones"],
    },
    {
        "clue": "You squeeze it and something comes out.",
        "answer": "toothpaste",
        "aliases": ["tooth paste"],
    },
    {
        "clue": "You put it between your lips before you blow.",
        "answer": "whistle",
        "aliases": ["a whistle"],
    },
    {
        "clue": "It has a handle and you use it to sweep.",
        "answer": "broom",
        "aliases": ["a broom"],
    },
    {
        "clue": "You pull its cord to make it start.",
        "answer": "lawn mower",
        "aliases": ["lawnmower"],
    },
    {
        "clue": "You sit in it and move it with your feet.",
        "answer": "swing",
        "aliases": ["a swing"],
    },


    # ======================================================
    # 26-50
    # ======================================================

    {
        "clue": "You shake me before you use me.",
        "answer": "paint can",
        "aliases": ["paintcan", "can of paint"],
    },
    {
        "clue": "You pump me until I'm firm.",
        "answer": "bicycle tire",
        "aliases": ["bike tire", "bicycle tyre", "bike tyre"],
    },
    {
        "clue": "I have a shaft and a point.",
        "answer": "pencil",
        "aliases": ["a pencil"],
    },
    {
        "clue": "You sharpen me before you use me.",
        "answer": "pencil",
        "aliases": ["a pencil"],
    },
    {
        "clue": "I'm stiff when I'm cold and soft when I'm warm.",
        "answer": "butter",
        "aliases": ["a stick of butter"],
    },
    {
        "clue": "You spread me all over your toast.",
        "answer": "butter",
        "aliases": ["a stick of butter"],
    },
    {
        "clue": "I come in a tube and you squeeze me out.",
        "answer": "toothpaste",
        "aliases": ["tooth paste"],
    },
    {
        "clue": "You put me between your teeth and pull.",
        "answer": "dental floss",
        "aliases": ["floss"],
    },
    {
        "clue": "You brush me every morning and night.",
        "answer": "teeth",
        "aliases": ["your teeth"],
    },
    {
        "clue": "I have bristles and you run me through your hair.",
        "answer": "hairbrush",
        "aliases": ["hair brush", "brush"],
    },
    {
        "clue": "The more you stroke me, the smoother I get.",
        "answer": "hair",
        "aliases": ["your hair"],
    },
    {
        "clue": "I have a handle and you use me to clean yourself.",
        "answer": "loofah",
        "aliases": ["bath loofah", "loofa"],
    },
    {
        "clue": "You squeeze me and water comes out.",
        "answer": "sponge",
        "aliases": ["a sponge"],
    },
    {
        "clue": "I get hot when you turn me on.",
        "answer": "hair dryer",
        "aliases": ["hairdryer", "blow dryer", "blowdryer"],
    },
    {
        "clue": "You put me on before going out.",
        "answer": "perfume",
        "aliases": ["fragrance"],
    },
    {
        "clue": "One spray and everyone knows you're nearby.",
        "answer": "cologne",
        "aliases": ["fragrance"],
    },
    {
        "clue": "You rub me on your lips.",
        "answer": "lip balm",
        "aliases": ["chapstick", "lipbalm"],
    },
    {
        "clue": "I come in different flavors and melt in your mouth.",
        "answer": "candy",
        "aliases": ["sweet", "sweets"],
    },
    {
        "clue": "You suck on me when you want something sweet.",
        "answer": "lollipop",
        "aliases": ["lolly pop", "lolly"],
    },
    {
        "clue": "You unwrap me before you put me in your mouth.",
        "answer": "candy",
        "aliases": ["sweet"],
    },
    {
        "clue": "I'm hot, steamy, and everyone wants me in the morning.",
        "answer": "coffee",
        "aliases": ["a cup of coffee"],
    },
    {
        "clue": "You pour me over something before you eat it.",
        "answer": "syrup",
        "aliases": ["maple syrup"],
    },
    {
        "clue": "I'm sticky and you lick your fingers after eating me.",
        "answer": "honey",
        "aliases": ["a honey"],
    },
    {
        "clue": "You pull me toward you when you want me closer.",
        "answer": "chair",
        "aliases": ["a chair"],
    },
    {
        "clue": "I have a hole in the middle and you hold me with two fingers.",
        "answer": "button",
        "aliases": ["a button"],
    },


    # ======================================================
    # 51-75
    # ======================================================

    {
        "clue": "I get tighter when you pull both ends.",
        "answer": "shoelace",
        "aliases": ["shoe lace", "laces"],
    },
    {
        "clue": "You tie me before you go outside.",
        "answer": "shoelace",
        "aliases": ["shoe lace", "laces"],
    },
    {
        "clue": "I hang around your neck but I'm not jewelry.",
        "answer": "scarf",
        "aliases": ["a scarf"],
    },
    {
        "clue": "You wrap me around yourself when you're cold.",
        "answer": "blanket",
        "aliases": ["a blanket"],
    },
    {
        "clue": "I'm soft, fluffy, and you love to squeeze me.",
        "answer": "pillow",
        "aliases": ["a pillow"],
    },
    {
        "clue": "You lay your head on me every night.",
        "answer": "pillow",
        "aliases": ["a pillow"],
    },
    {
        "clue": "You get under me when you go to bed.",
        "answer": "blanket",
        "aliases": ["a blanket"],
    },
    {
        "clue": "I can be stuffed, fluffy, and cuddly.",
        "answer": "stuffed animal",
        "aliases": ["stuffed toy", "plushie", "plush toy"],
    },
    {
        "clue": "You put me on your finger before using me.",
        "answer": "glove",
        "aliases": ["a glove"],
    },
    {
        "clue": "I cover your hand but leave your fingers together.",
        "answer": "mitten",
        "aliases": ["a mitten"],
    },
    {
        "clue": "You slip me on before you leave the house.",
        "answer": "shoe",
        "aliases": ["shoes"],
    },
    {
        "clue": "I come off when you pull my tongue.",
        "answer": "shoe",
        "aliases": ["shoes"],
    },
    {
        "clue": "You stuff your foot inside me.",
        "answer": "sock",
        "aliases": ["socks"],
    },
    {
        "clue": "I have a tongue but can't talk.",
        "answer": "shoe",
        "aliases": ["shoes"],
    },
    {
        "clue": "You polish me until I shine.",
        "answer": "shoe",
        "aliases": ["shoes"],
    },
    {
        "clue": "I have a heel but no foot.",
        "answer": "shoe",
        "aliases": ["shoes"],
    },
    {
        "clue": "You kick me around for fun.",
        "answer": "ball",
        "aliases": ["a ball"],
    },
    {
        "clue": "You bounce me before you shoot.",
        "answer": "basketball",
        "aliases": ["basket ball"],
    },
    {
        "clue": "You swing me before you hit the ball.",
        "answer": "bat",
        "aliases": ["baseball bat"],
    },
    {
        "clue": "I have a handle and you grip me tightly.",
        "answer": "baseball bat",
        "aliases": ["bat"],
    },
    {
        "clue": "You throw me and someone catches me.",
        "answer": "ball",
        "aliases": ["a ball"],
    },
    {
        "clue": "I get tossed around at parties.",
        "answer": "ball",
        "aliases": ["a ball"],
    },
    {
        "clue": "You blow me before you eat.",
        "answer": "birthday candle",
        "aliases": ["candle", "birthday candles"],
    },
    {
        "clue": "I get shorter the longer you use me.",
        "answer": "candle",
        "aliases": ["a candle"],
    },
    {
        "clue": "I melt when things get hot.",
        "answer": "candle",
        "aliases": ["wax candle"],
    },


    # ======================================================
    # 76-100
    # ======================================================

    {
        "clue": "You stick me into a cake.",
        "answer": "candle",
        "aliases": ["birthday candle"],
    },
    {
        "clue": "You light me before the fun begins.",
        "answer": "candle",
        "aliases": ["a candle"],
    },
    {
        "clue": "I have a flame on top and wax underneath.",
        "answer": "candle",
        "aliases": ["a candle"],
    },
    {
        "clue": "You rub me between your hands to make bubbles.",
        "answer": "soap",
        "aliases": ["bar of soap"],
    },
    {
        "clue": "I get smaller every time you use me.",
        "answer": "bar of soap",
        "aliases": ["soap"],
    },
    {
        "clue": "I get slippery when wet.",
        "answer": "soap",
        "aliases": ["bar of soap"],
    },
    {
        "clue": "You rub me all over before rinsing.",
        "answer": "soap",
        "aliases": ["bar of soap"],
    },
    {
        "clue": "I come in a bottle and make your hair slippery.",
        "answer": "shampoo",
        "aliases": ["hair shampoo"],
    },
    {
        "clue": "You massage me into your scalp.",
        "answer": "shampoo",
        "aliases": ["hair shampoo"],
    },
    {
        "clue": "You rinse me out after rubbing me in.",
        "answer": "conditioner",
        "aliases": ["hair conditioner"],
    },
    {
        "clue": "I make your hair soft after you use me.",
        "answer": "conditioner",
        "aliases": ["hair conditioner"],
    },
    {
        "clue": "You squeeze me onto your hand before washing.",
        "answer": "hand soap",
        "aliases": ["soap"],
    },
    {
        "clue": "I come out when you push my top.",
        "answer": "soap dispenser",
        "aliases": ["soap pump", "dispenser"],
    },
    {
        "clue": "You push me in until it clicks.",
        "answer": "button",
        "aliases": ["a button"],
    },
    {
        "clue": "I pop when you push me too hard.",
        "answer": "bubble wrap",
        "aliases": ["bubblewrap"],
    },
    {
        "clue": "You squeeze me until I pop.",
        "answer": "bubble wrap",
        "aliases": ["bubblewrap"],
    },
    {
        "clue": "I'm full of air and fun to pop.",
        "answer": "bubble",
        "aliases": ["a bubble"],
    },
    {
        "clue": "You blow me and I disappear.",
        "answer": "bubble",
        "aliases": ["a bubble"],
    },
    {
        "clue": "I can be popped but I don't make popcorn.",
        "answer": "bubble",
        "aliases": ["a bubble"],
    },
    {
        "clue": "You rub me and I disappear.",
        "answer": "eraser",
        "aliases": ["rubber"],
    },
    {
        "clue": "The harder you press me, the darker I get.",
        "answer": "pencil",
        "aliases": ["a pencil"],
    },
    {
        "clue": "You hold me between your fingers while you write.",
        "answer": "pencil",
        "aliases": ["a pencil"],
    },
    {
        "clue": "I have a tip that gets shorter every time you use me.",
        "answer": "pencil",
        "aliases": ["a pencil"],
    },
    {
        "clue": "You can slide me in and out of a sleeve.",
        "answer": "arm",
        "aliases": ["your arm"],
    },
    {
        "clue": "You pull me open when you want to get inside.",
        "answer": "zipper",
        "aliases": ["zip"],
    },


    # ======================================================
    # 101-125
    # ======================================================

    {
        "clue": "I'm usually hidden under your clothes.",
        "answer": "pocket",
        "aliases": ["a pocket"],
    },
    {
        "clue": "You can unzip me from either end.",
        "answer": "jacket",
        "aliases": ["coat"],
    },
    {
        "clue": "I have a long neck and you can squeeze me.",
        "answer": "ketchup bottle",
        "aliases": ["ketchup", "ketchup container"],
    },
    {
        "clue": "You turn me to make something happen.",
        "answer": "knob",
        "aliases": ["a knob"],
    },
    {
        "clue": "You twist me when you want water.",
        "answer": "faucet",
        "aliases": ["tap", "water faucet"],
    },
    {
        "clue": "You turn me and water comes out.",
        "answer": "faucet",
        "aliases": ["tap", "water tap"],
    },
    {
        "clue": "You pull me down before the water starts.",
        "answer": "shower handle",
        "aliases": ["shower knob", "shower control"],
    },
    {
        "clue": "I spray when you squeeze my trigger.",
        "answer": "spray bottle",
        "aliases": ["spraybottle"],
    },
    {
        "clue": "You squeeze me to make your plants happy.",
        "answer": "watering bottle",
        "aliases": ["spray bottle", "water bottle"],
    },
    {
        "clue": "I have a nozzle and you squeeze me to make a mist.",
        "answer": "spray bottle",
        "aliases": ["spraybottle"],
    },
    {
        "clue": "You stick me in the ground before you water me.",
        "answer": "garden hose",
        "aliases": ["hose"],
    },
    {
        "clue": "I get twisted, kinked, and stretched across the yard.",
        "answer": "garden hose",
        "aliases": ["hose"],
    },
    {
        "clue": "You roll me up when you're finished with me.",
        "answer": "garden hose",
        "aliases": ["hose"],
    },
    {
        "clue": "You squeeze my handle and I make a loud noise.",
        "answer": "bike horn",
        "aliases": ["horn", "bicycle horn"],
    },
    {
        "clue": "You pull my lever before I make a sound.",
        "answer": "bell",
        "aliases": ["hand bell"],
    },
    {
        "clue": "I have a handle and a metal head.",
        "answer": "hammer",
        "aliases": ["a hammer"],
    },
    {
        "clue": "You hit me with another object until I go in.",
        "answer": "nail",
        "aliases": ["a nail"],
    },
    {
        "clue": "You pull me out when you want to remove something.",
        "answer": "nail",
        "aliases": ["a nail"],
    },
    {
        "clue": "You drive me into wood.",
        "answer": "nail",
        "aliases": ["a nail"],
    },
    {
        "clue": "You screw me in and turn me until I'm tight.",
        "answer": "screw",
        "aliases": ["a screw"],
    },
    {
        "clue": "I have a head and threads.",
        "answer": "screw",
        "aliases": ["a screw"],
    },
    {
        "clue": "You turn me with a screwdriver.",
        "answer": "screw",
        "aliases": ["a screw"],
    },
    {
        "clue": "You push me through a hole to hold things together.",
        "answer": "bolt",
        "aliases": ["a bolt"],
    },
    {
        "clue": "You tighten me with a wrench.",
        "answer": "bolt",
        "aliases": ["a bolt"],
    },
    {
        "clue": "I have a hole in me and go onto a bolt.",
        "answer": "nut",
        "aliases": ["a nut"],
    },


    # ======================================================
    # 126-150
    # ======================================================

    {
        "clue": "You crack me before you cook me.",
        "answer": "egg",
        "aliases": ["an egg"],
    },
    {
        "clue": "I'm white on the outside and yellow inside.",
        "answer": "egg",
        "aliases": ["an egg"],
    },
    {
        "clue": "You beat me before putting me in a pan.",
        "answer": "egg",
        "aliases": ["an egg", "eggs"],
    },
    {
        "clue": "You whip me until I becomes fluffy.",
        "answer": "cream",
        "aliases": ["whipping cream"],
    },
    {
        "clue": "You spread me on bread and I can be soft or hard.",
        "answer": "cheese",
        "aliases": ["a slice of cheese"],
    },
    {
        "clue": "I come in a block and you can grate me.",
        "answer": "cheese",
        "aliases": ["block of cheese"],
    },
    {
        "clue": "You grate me over pasta.",
        "answer": "parmesan",
        "aliases": ["parmesan cheese", "cheese"],
    },
    {
        "clue": "I'm long, thin, and you twirl me around a fork.",
        "answer": "spaghetti",
        "aliases": ["pasta"],
    },
    {
        "clue": "You roll me before putting me in the oven.",
        "answer": "dough",
        "aliases": ["bread dough"],
    },
    {
        "clue": "The more you knead me, the smoother I become.",
        "answer": "dough",
        "aliases": ["bread dough"],
    },
    {
        "clue": "You punch me down after I rise.",
        "answer": "dough",
        "aliases": ["bread dough"],
    },
    {
        "clue": "You stick me in a hole to see how deep it is.",
        "answer": "measuring stick",
        "aliases": ["stick", "rod"],
    },
    {
        "clue": "I have a long handle and you use me to stir.",
        "answer": "spoon",
        "aliases": ["wooden spoon"],
    },
    {
        "clue": "You put me in your mouth to taste the food.",
        "answer": "spoon",
        "aliases": ["a spoon"],
    },
    {
        "clue": "You lick me clean when you're finished.",
        "answer": "spoon",
        "aliases": ["a spoon"],
    },
    {
        "clue": "You dip me before you take a bite.",
        "answer": "chip",
        "aliases": ["potato chip", "tortilla chip"],
    },
    {
        "clue": "I'm crunchy, salty, and easy to put in your mouth.",
        "answer": "chip",
        "aliases": ["potato chip", "tortilla chip"],
    },
    {
        "clue": "You put me in a cup before pouring something hot over me.",
        "answer": "tea bag",
        "aliases": ["teabag"],
    },
    {
        "clue": "I get stronger the longer you leave me in hot water.",
        "answer": "tea bag",
        "aliases": ["teabag"],
    },
    {
        "clue": "You squeeze me before putting me in your drink.",
        "answer": "lemon",
        "aliases": ["lemon wedge"],
    },
    {
        "clue": "You roll me before you cut me.",
        "answer": "dough",
        "aliases": ["bread dough"],
    },
    {
        "clue": "You peel me before you eat me.",
        "answer": "banana",
        "aliases": ["a banana"],
    },
    {
        "clue": "I'm long, curved, and yellow when I'm ready.",
        "answer": "banana",
        "aliases": ["a banana"],
    },
    {
        "clue": "You squeeze me and I make a loud squeak.",
        "answer": "dog toy",
        "aliases": ["squeaky toy", "squeaker toy"],
    },
    {
        "clue": "You throw me for the dog and it brings me back.",
        "answer": "frisbee",
        "aliases": ["disc", "flying disc"],
    },
]


# ==========================================================
# CLUE BANK VALIDATION
# ==========================================================

def validate_clue_bank() -> None:
    """
    Validate the clue bank when this module is loaded.

    This catches accidental malformed clues during development.
    """

    if len(DIRTY_MINDS_CLUES) < 100:
        raise RuntimeError(
            "Dirty Minds clue bank must contain at least 100 clues."
        )

    for index, clue in enumerate(DIRTY_MINDS_CLUES, start=1):

        if not isinstance(clue, dict):
            raise RuntimeError(
                f"Dirty Minds clue #{index} is not a dictionary."
            )

        if not clue.get("clue"):
            raise RuntimeError(
                f"Dirty Minds clue #{index} has no clue text."
            )

        if not clue.get("answer"):
            raise RuntimeError(
                f"Dirty Minds clue #{index} has no answer."
            )

        if "aliases" not in clue:
            clue["aliases"] = []

        if not isinstance(clue["aliases"], list):
            raise RuntimeError(
                f"Dirty Minds clue #{index} aliases must be a list."
            )


validate_clue_bank()


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def normalize_answer(value: Any) -> str:
    """
    Normalize an answer for comparison.

    Examples:
        "A Toothbrush!" -> "toothbrush"
        "TOOTH BRUSH"  -> "toothbrush"
        "the pillow"   -> "pillow"
    """

    if value is None:
        return ""

    text = str(value).strip().lower()

    # Remove punctuation.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    # Remove common leading articles.
    text = re.sub(
        r"^(a|an|the)\s+",
        "",
        text,
    )

    # Remove spaces for comparison.
    return text.replace(" ", "")


def _build_answer_keys(
    clue: dict[str, Any],
) -> set[str]:
    """
    Build all accepted normalized answers for a clue.
    """

    keys = {
        normalize_answer(
            clue.get("answer", "")
        ),
    }

    for alias in clue.get("aliases", []):
        normalized = normalize_answer(alias)

        if normalized:
            keys.add(normalized)

    return {
        key
        for key in keys
        if key
    }


def answer_is_correct(
    clue: dict[str, Any],
    answer: str,
) -> bool:
    """
    Check a submitted answer against the clue.
    """

    submitted = normalize_answer(answer)

    if not submitted:
        return False

    return submitted in _build_answer_keys(clue)


# ==========================================================
# GAME STATE
# ==========================================================

def create_dirty_minds_state() -> dict[str, Any]:
    """
    Create a brand-new Dirty Minds state.
    """

    return {
        "status": "waiting",

        "round": 0,
        "total_rounds": TOTAL_ROUNDS,

        # Selected clues for this game.
        "rounds": [],

        # Current clue.
        "current_clue": "",
        "current_answer": "",

        # Submitted answers.
        #
        # Key:
        #   player_key
        #
        # Value:
        #   {
        #       "answer": "...",
        #       "correct": True/False,
        #       "submitted_at": timestamp
        #   }
        #
        # This remains server-side.
        "answers": {},

        "revealed": False,

        "round_winner": None,

        "round_started_at": None,

        # Results become available only after reveal.
        "round_results": [],

        # Final winner.
        "winner": None,

        "game_started_at": None,
        "game_finished_at": None,
    }


# ==========================================================
# ROUND CREATION
# ==========================================================

def _select_rounds() -> list[dict[str, Any]]:
    """
    Randomly select the clues for a game.
    """

    count = min(
        TOTAL_ROUNDS,
        len(DIRTY_MINDS_CLUES),
    )

    selected = random.sample(
        DIRTY_MINDS_CLUES,
        count,
    )

    # Copy dictionaries so the original clue bank
    # can never be modified accidentally.
    return [
        {
            "clue": item["clue"],
            "answer": item["answer"],
            "aliases": list(
                item.get("aliases", [])
            ),
        }
        for item in selected
    ]


def _load_current_round(room) -> None:
    """
    Load the current round into the room state.
    """

    state = room.state

    round_number = int(
        state.get("round", 0)
    )

    rounds = state.get(
        "rounds",
        []
    )

    if round_number < 1:
        raise ValueError(
            "Invalid round number."
        )

    if round_number > len(rounds):
        raise ValueError(
            "Round does not exist."
        )

    current = rounds[
        round_number - 1
    ]

    state["current_clue"] = current["clue"]

    state["current_answer"] = current["answer"]

    state["answers"] = {}

    state["revealed"] = False

    state["round_winner"] = None

    state["round_results"] = []

    state["round_started_at"] = time.time()

    room.touch()


# ==========================================================
# START GAME
# ==========================================================

def start_game(room) -> dict[str, Any]:
    """
    Start or restart a Dirty Minds game.

    Host validation should be performed by the Flask route.
    """

    if room.player_count() < room.min_players:
        raise ValueError(
            f"At least {room.min_players} players are required."
        )

    rounds = _select_rounds()

    room.state = create_dirty_minds_state()

    room.state["status"] = "playing"

    room.state["round"] = 1

    room.state["total_rounds"] = len(rounds)

    room.state["rounds"] = rounds

    room.state["game_started_at"] = time.time()

    room.started = True

    room.finished = False

    room.winner_id = None

    room.reset_scores()

    _load_current_round(room)

    return public_room_state(room)


# ==========================================================
# SUBMIT ANSWER
# ==========================================================

def submit_answer(
    room,
    player_key: str,
    answer: str,
) -> dict[str, Any]:
    """
    Submit one answer for the current round.

    Each player may submit only once per round.
    """

    player = room.get_player_by_key(
        player_key
    )

    if not player:
        raise ValueError(
            "Player is not in this game."
        )

    state = room.state

    if state.get("status") != "playing":
        raise ValueError(
            "This round is not accepting answers."
        )

    if state.get("revealed"):
        raise ValueError(
            "The answer has already been revealed."
        )

    answer = str(
        answer or ""
    ).strip()

    if not answer:
        raise ValueError(
            "Please enter an answer."
        )

    if len(answer) > 100:
        raise ValueError(
            "Answer is too long."
        )

    answers = state.setdefault(
        "answers",
        {}
    )

    if player_key in answers:
        raise ValueError(
            "You already submitted an answer this round."
        )

    round_number = int(
        state.get("round", 0)
    )

    rounds = state.get(
        "rounds",
        []
    )

    if (
        not round_number
        or round_number > len(rounds)
    ):
        raise ValueError(
            "Invalid current round."
        )

    clue = rounds[
        round_number - 1
    ]

    answers[player_key] = {
        "answer": answer,
        "correct": None,
        "result": None,
        "points": 0.0,
        "graded": False,
        "submitted_at": time.time(),
    }

    room.touch()

    return {
        "success": True,
        "submitted": True,
        "correct": None,
        "message": "✅ Answer submitted. The host will grade it after the reveal.",
        "state": public_room_state(
            room,
            player_key=player_key,
        ),
    }


# ==========================================================
# REVEAL ROUND
# ==========================================================

def reveal_round(room) -> dict[str, Any]:
    """Reveal the answer and expose all submitted answers.

    Scoring is intentionally NOT automatic. The host grades each
    submitted answer as correct (1), partial (0.5), or wrong (0).
    """
    state = room.state
    if state.get("status") != "playing":
        raise ValueError("This round is not active.")
    if state.get("revealed"):
        return public_room_state(room)

    round_number = int(state.get("round", 0))
    rounds = state.get("rounds", [])
    if round_number < 1 or round_number > len(rounds):
        raise ValueError("Invalid current round.")

    results = []
    answers = state.get("answers", {})
    for player_key, submission in answers.items():
        player = room.get_player_by_key(player_key)
        if not player:
            continue
        results.append({
            "player_key": player_key,
            "name": player.get("name", "Player"),
            "answer": submission.get("answer", ""),
            "result": submission.get("result"),
            "points": float(submission.get("points", 0.0)),
            "graded": bool(submission.get("graded", False)),
        })

    submitted_keys = set(answers.keys())
    for player in room.players.values():
        key = player.get("player_key")
        if key in submitted_keys:
            continue
        results.append({
            "player_key": key,
            "name": player.get("name", "Player"),
            "answer": "",
            "result": "wrong",
            "points": 0.0,
            "graded": True,
            "did_not_answer": True,
        })

    state["revealed"] = True
    state["status"] = "revealed"
    state["round_results"] = results
    room.touch()
    return public_room_state(room)


# ==========================================================
# GRADE ANSWER
# ==========================================================

def grade_answer(room, host_player_key: str, target_player_key: str, grade: str) -> dict[str, Any]:
    """Host grades one submitted answer: correct=1, partial=0.5, wrong=0."""
    host = room.get_player_by_key(host_player_key)
    if not host or not host.get("host", False):
        raise ValueError("Only the host can grade answers.")

    state = room.state
    if not state.get("revealed") or state.get("status") != "revealed":
        raise ValueError("Reveal the round before grading answers.")

    if grade not in {"correct", "partial", "wrong"}:
        raise ValueError("Invalid grade.")

    submission = state.get("answers", {}).get(target_player_key)
    player = room.get_player_by_key(target_player_key)
    if not submission or not player:
        raise ValueError("Submitted answer not found.")

    if submission.get("graded"):
        raise ValueError("That answer has already been graded.")

    points = {"correct": 1.0, "partial": 0.5, "wrong": 0.0}[grade]
    submission["result"] = grade
    submission["points"] = points
    submission["correct"] = grade == "correct"
    submission["graded"] = True

    # Dirty Minds supports half-points.  The generic GameRoom score helper
    # converts points to int, which would turn 0.5 into 0.  Keep the score
    # directly on the player as a float so both +1 and +0.5 are preserved.
    current_score = float(player.get("score", 0) or 0)
    player["score"] = current_score + points
    room.touch()

    # Rebuild visible results and determine the round winner.
    results = []
    best = -1.0
    winners = []
    for key, sub in state.get("answers", {}).items():
        pl = room.get_player_by_key(key)
        if not pl:
            continue
        pts = float(sub.get("points", 0.0))
        results.append({
            "player_key": key,
            "name": pl.get("name", "Player"),
            "answer": sub.get("answer", ""),
            "result": sub.get("result"),
            "points": pts,
            "graded": bool(sub.get("graded", False)),
        })
        if sub.get("graded"):
            if pts > best:
                best = pts; winners = [pl]
            elif pts == best:
                winners.append(pl)
    if best > 0 and winners:
        state["round_winner"] = winners[0]["user_id"] if len(winners) == 1 else None
    state["round_results"] = results
    room.touch()
    return {"success": True, "graded": True, "grade": grade, "points": points, "state": public_room_state(room, player_key=host_player_key)}

# ==========================================================
# NEXT ROUND
# ==========================================================

def next_round(room) -> dict[str, Any]:
    """
    Advance to the next round.

    Host-only validation should be performed by the Flask route.
    """

    state = room.state

    status = state.get(
        "status"
    )

    if status != "revealed":
        raise ValueError(
            "Reveal the answer before starting the next round."
        )

    # Every submitted answer must be explicitly graded before the host
    # can advance.  This prevents the Next Round button from silently
    # awarding 0 points to an answer the host forgot to grade.
    ungraded = [
        submission
        for submission in state.get("answers", {}).values()
        if not submission.get("graded", False)
    ]
    if ungraded:
        raise ValueError(
            "Grade all submitted answers before starting the next round."
        )

    current_round = int(
        state.get("round", 0)
    )

    total_rounds = int(
        state.get(
            "total_rounds",
            TOTAL_ROUNDS,
        )
    )

    if current_round >= total_rounds:
        return finish_game(room)

    state["round"] = (
        current_round + 1
    )

    _load_current_round(room)

    state["status"] = "playing"

    room.touch()

    return public_room_state(room)


# ==========================================================
# FINISH GAME
# ==========================================================

def finish_game(room) -> dict[str, Any]:
    """
    Finish the game and determine the winner.
    """

    state = room.state

    state["status"] = "finished"

    state["revealed"] = True

    state["game_finished_at"] = time.time()

    # Sort highest score first.
    players = sorted(
        room.players.values(),
        key=lambda player: (
            float(player.get("score", 0) or 0),
            -float(
                player.get(
                    "joined_at",
                    0,
                )
            ),
        ),
        reverse=True,
    )

    winner = None

    if players:

        top_score = float(players[0].get("score", 0) or 0)

        # Tie handling.
        tied = [
            player
            for player in players
            if float(player.get("score", 0) or 0) == top_score
        ]

        if len(tied) == 1:

            winner = {
                "name": tied[0].get(
                    "name",
                    "Player",
                ),
                "score": top_score,
            }

            room.winner_id = tied[0][
                "user_id"
            ]

        else:

            winner = {
                "name": "Tie Game",
                "score": top_score,
                "players": [
                    player.get(
                        "name",
                        "Player",
                    )
                    for player in tied
                ],
            }

            room.winner_id = None

    state["winner"] = winner

    room.finished = True

    room.touch()

    return public_room_state(room)


# ==========================================================
# RESET GAME
# ==========================================================

def reset_game(room) -> dict[str, Any]:
    """
    Reset a Dirty Minds room back to waiting.

    Useful if the host wants to start a completely new game.
    """

    room.state = create_dirty_minds_state()

    room.started = False

    room.finished = False

    room.winner_id = None

    room.reset_scores()

    room.touch()

    return public_room_state(room)


# ==========================================================
# PLAYER-SPECIFIC INFORMATION
# ==========================================================

def _player_submission(
    room,
    player_key: str | None,
) -> dict[str, Any] | None:
    """
    Get the current player's submission.
    """

    if not player_key:
        return None

    return room.state.get(
        "answers",
        {}
    ).get(
        player_key
    )


# ==========================================================
# PUBLIC GAME STATE
# ==========================================================

def public_room_state(
    room,
    player_key: str | None = None,
) -> dict[str, Any]:
    """
    Return information safe to send to a browser.

    IMPORTANT:
    The correct answer is hidden until the round is revealed.
    """

    state = room.state

    status = state.get(
        "status",
        "waiting",
    )

    revealed = bool(
        state.get(
            "revealed",
            False,
        )
    )

    current_answer = ""

    if revealed:
        current_answer = state.get(
            "current_answer",
            "",
        )

    submission = _player_submission(
        room,
        player_key,
    )

    my_submitted = (
        submission is not None
    )

    my_correct = None
    my_result = None
    my_points = 0.0
    if submission is not None and revealed and submission.get("graded"):
        my_correct = bool(submission.get("correct", False))
        my_result = submission.get("result")
        my_points = float(submission.get("points", 0.0))

    # Build player list without exposing:
    #
    #   - Telegram user IDs
    #   - player keys
    #   - internal timestamps
    #
    players = []

    for player in room.players.values():

        players.append(
            {
                "name": player.get(
                    "name",
                    "Player",
                ),
                "score": float(player.get("score", 0) or 0),
                "host": bool(
                    player.get(
                        "host",
                        False,
                    )
                ),
            }
        )

    result = {
        "room_id": room.room_id,

        "game_id": room.game_id,

        "game_name": room.game_name,

        "status": status,

        "round": int(
            state.get(
                "round",
                0,
            )
        ),

        "total_rounds": int(
            state.get(
                "total_rounds",
                TOTAL_ROUNDS,
            )
        ),

        "clue": state.get(
            "current_clue",
            "",
        ),

        # Answer remains hidden until reveal.
        "answer": current_answer,

        "revealed": revealed,

        "player_count": room.player_count(),

        "max_players": room.max_players,

        "min_players": room.min_players,

        "players": players,

        "submitted_count": len(
            state.get(
                "answers",
                {},
            )
        ),

        "my_submitted": my_submitted,

        "my_correct": my_correct,
        "my_result": my_result,
        "my_points": my_points,
        "round_winner": None,
        "submissions": [],

        "round_results": [],

        "winner": state.get(
            "winner"
        ),

        "started": bool(
            room.started
        ),

        "finished": bool(
            room.finished
        ),

        "is_host": False,

        "can_start": False,

        "can_reveal": False,

        "can_next": False,
    }

    # ======================================================
    # CURRENT PLAYER HOST STATUS
    # ======================================================

    if player_key:

        player = room.get_player_by_key(
            player_key
        )

        if player:

            result["is_host"] = bool(
                player.get(
                    "host",
                    False,
                )
            )

    # ======================================================
    # HOST CONTROLS
    # ======================================================

    result["can_start"] = (
        result["is_host"]
        and status in {
            "waiting",
            "finished",
        }
        and room.player_count()
        >= room.min_players
    )

    result["can_reveal"] = (
        result["is_host"]
        and status == "playing"
        and not revealed
    )

    result["can_next"] = (
        result["is_host"]
        and status == "revealed"
        and all(item.get("graded", False) for item in state.get("answers", {}).values())
    )

    # Only the host may see submitted answers before grading is complete.
    if result["is_host"] and status == "revealed":
        result["submissions"] = [
            {
                "player_key": key,
                "name": room.get_player_by_key(key).get("name", "Player") if room.get_player_by_key(key) else "Player",
                "answer": sub.get("answer", ""),
                "result": sub.get("result"),
                "points": float(sub.get("points", 0.0)),
                "graded": bool(sub.get("graded", False)),
            }
            for key, sub in state.get("answers", {}).items()
            if room.get_player_by_key(key)
        ]

    # ======================================================
    # REVEAL INFORMATION
    # ======================================================

    if revealed:

        result["round_winner"] = state.get(
            "round_winner"
        )

        result["round_results"] = list(
            state.get(
                "round_results",
                [],
            )
        )

    return result


# ==========================================================
# UTILITY FUNCTIONS
# ==========================================================

def get_current_clue(
    room,
) -> dict[str, Any] | None:
    """
    Return the current clue internally.

    This should NOT be sent directly to the browser because
    it contains the answer.
    """

    state = room.state

    round_number = int(
        state.get(
            "round",
            0,
        )
    )

    rounds = state.get(
        "rounds",
        []
    )

    if round_number < 1:
        return None

    if round_number > len(rounds):
        return None

    return rounds[
        round_number - 1
    ]


def get_correct_answer(
    room,
) -> str:
    """
    Get the correct answer internally.
    """

    return str(
        room.state.get(
            "current_answer",
            "",
        )
    )


def player_has_submitted(
    room,
    player_key: str,
) -> bool:
    """
    Check whether a player has submitted an answer
    for the current round.
    """

    if not player_key:
        return False

    return player_key in room.state.get(
        "answers",
        {},
    )


def all_players_submitted(
    room,
) -> bool:
    """
    Return True when every player has submitted.

    Returns False when the room has no players.
    """

    player_count = room.player_count()

    if player_count == 0:
        return False

    submitted_count = len(
        room.state.get(
            "answers",
            {},
        )
    )

    return submitted_count >= player_count


# ==========================================================
# CLUE BANK INFORMATION
# ==========================================================

def get_clue_count() -> int:
    """
    Return the number of clues currently available.
    """

    return len(DIRTY_MINDS_CLUES)


def get_random_clue() -> dict[str, Any]:
    """
    Return a random clue.

    Intended for internal use.
    """

    return random.choice(
        DIRTY_MINDS_CLUES
    )
