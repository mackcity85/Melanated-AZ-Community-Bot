# ==========================================================
# Melanated AZ Bot
# games/game_data.py
#
# Shared game content for the Games category
#
# IMPORTANT:
#   - This file contains GAME DATA ONLY.
#   - It does not import from bot.py or admin.py.
#   - It is safe to import from the individual game modules.
# ==========================================================


# ==========================================================
# GAME DEFINITIONS
# ==========================================================

GAME_DEFINITIONS = {
    "truth_dare": {
        "name": "🔥 Truth or Dare",
        "description": "Fun, flirty, spicy and adventurous Truth or Dare.",
        "command": "truthdare",
        "callback": "game_truthdare",
    },

    "would_you_rather": {
        "name": "🤔 Would You Rather",
        "description": "Choose between two fun, wild or spicy options.",
        "command": "wouldyourather",
        "callback": "game_wyr",
    },

    "never_have_i_ever": {
        "name": "🙈 Never Have I Ever",
        "description": "See who has done it and who hasn't.",
        "command": "neverhaveiever",
        "callback": "game_nhie",
    },

    "most_likely": {
        "name": "👀 Most Likely To",
        "description": "Vote on who is most likely to do it.",
        "command": "mostlikely",
        "callback": "game_mostlikely",
    },

    "this_or_that": {
        "name": "⚡ This or That",
        "description": "Pick one. No overthinking.",
        "command": "thisorthat",
        "callback": "game_thisorthat",
    },

    "hot_seat": {
        "name": "🔥 Hot Seat",
        "description": "One player gets the spotlight.",
        "command": "hotseat",
        "callback": "game_hotseat",
    },

    "confession": {
        "name": "🤫 Confessions",
        "description": "Share a confession. Keep it respectful.",
        "command": "confession",
        "callback": "game_confession",
    },

    "compliment_battle": {
        "name": "💜 Compliment Battle",
        "description": "Bring the good energy with compliments.",
        "command": "complimentbattle",
        "callback": "game_compliment",
    },

    "dice": {
        "name": "🎲 Dice Game",
        "description": "Roll the dice and see what happens.",
        "command": "gamedice",
        "callback": "game_dice",
    },

    "coin_flip": {
        "name": "🪙 Coin Flip",
        "description": "Heads or tails.",
        "command": "coinflip",
        "callback": "game_coinflip",
    },
}


# ==========================================================
# GENERAL GAME MESSAGES
# ==========================================================

GAME_MESSAGES = {
    "welcome": (
        "🎮 GAMES\n\n"
        "Welcome to the Melanated AZ Game Room!\n\n"
        "Choose a game below and have some fun. 😈\n\n"
        "💜 Keep it consensual.\n"
        "💜 Respect boundaries.\n"
        "💜 Anyone can PASS.\n"
        "💜 Keep the vibe fun."
    ),

    "disabled": (
        "🎮 Games are currently disabled by an administrator."
    ),

    "game_disabled": (
        "🎮 This game is currently disabled."
    ),

    "pass": (
        "😈 PASS accepted.\n\n"
        "No explanation required. Pick another option when you're ready."
    ),

    "back": "🎮 Back to Games",

    "choose_game": (
        "🎮 Choose a game:"
    ),

    "choose_level": (
        "🔥 Choose your level:"
    ),

    "error": (
        "⚠️ Something went wrong with that game.\n"
        "Please try again."
    ),
}


# ==========================================================
# WOULD YOU RATHER
# ==========================================================

WOULD_YOU_RATHER = {

    "mild": [
        (
            "Would you rather have a romantic dinner or a fun night out?",
            "🍷 Romantic dinner",
            "🎉 Night out",
        ),
        (
            "Would you rather make the first move or have someone approach you?",
            "😈 Make the move",
            "👀 Be approached",
        ),
        (
            "Would you rather go on a beach date or a city date?",
            "🏖️ Beach",
            "🌆 City",
        ),
        (
            "Would you rather receive flowers or your favorite snacks?",
            "🌹 Flowers",
            "🍫 Snacks",
        ),
        (
            "Would you rather stay home for date night or go somewhere new?",
            "🏠 Stay home",
            "🌎 Go somewhere new",
        ),
        (
            "Would you rather flirt through messages or face-to-face?",
            "📱 Messages",
            "👀 Face-to-face",
        ),
        (
            "Would you rather have great chemistry or great conversation?",
            "🔥 Chemistry",
            "💬 Conversation",
        ),
        (
            "Would you rather be the planner or the spontaneous one?",
            "📅 Planner",
            "🎲 Spontaneous",
        ),
        (
            "Would you rather receive a surprise date or plan your own?",
            "🎁 Surprise",
            "📝 Plan it",
        ),
        (
            "Would you rather dance together or cuddle during a movie?",
            "💃 Dance",
            "🎬 Cuddle",
        ),
    ],

    "spicy": [
        (
            "Would you rather spend the night flirting or teasing?",
            "😉 Flirting",
            "😈 Teasing",
        ),
        (
            "Would you rather make the first move or be chased?",
            "🔥 Make the move",
            "👀 Be chased",
        ),
        (
            "Would you rather have a slow-burn connection or instant chemistry?",
            "❤️ Slow burn",
            "🔥 Instant chemistry",
        ),
        (
            "Would you rather receive a seductive message or a whispered compliment?",
            "📱 Message",
            "😈 Whisper",
        ),
        (
            "Would you rather plan an adventurous night or let someone surprise you?",
            "🗓️ Plan it",
            "🎁 Surprise me",
        ),
        (
            "Would you rather flirt all night or build anticipation slowly?",
            "😉 All night",
            "🔥 Slowly",
        ),
        (
            "Would you rather be the tease or the one being teased?",
            "😈 Tease",
            "👀 Be teased",
        ),
        (
            "Would you rather have a private date or a group adventure?",
            "💜 Private",
            "🔥 Group",
        ),
        (
            "Would you rather be pursued or do the pursuing?",
            "👑 Pursued",
            "😈 Pursue",
        ),
        (
            "Would you rather have amazing conversation or undeniable chemistry?",
            "💬 Conversation",
            "🔥 Chemistry",
        ),
    ],

    "extreme": [
        (
            "Would you rather explore a new fantasy or revisit a favorite one?",
            "🔥 New fantasy",
            "😈 Favorite",
        ),
        (
            "Would you rather be completely spontaneous or plan every detail?",
            "🎲 Spontaneous",
            "📋 Planned",
        ),
        (
            "Would you rather explore with a trusted couple or a trusted single?",
            "👫 Couple",
            "🔥 Single",
        ),
        (
            "Would you rather be in control or give up control?",
            "👑 Control",
            "😈 Give it up",
        ),
        (
            "Would you rather have an adventurous weekend away or one unforgettable night?",
            "🌴 Weekend",
            "🔥 One night",
        ),
        (
            "Would you rather reveal a fantasy or hear someone else's fantasy?",
            "🤫 Reveal mine",
            "👀 Hear theirs",
        ),
        (
            "Would you rather try something completely new or perfect something you already love?",
            "🔥 New",
            "😈 Perfect it",
        ),
        (
            "Would you rather choose the adventure or let your partner choose?",
            "👑 My choice",
            "🎲 Their choice",
        ),
        (
            "Would you rather have intense chemistry or intense anticipation?",
            "🔥 Chemistry",
            "😈 Anticipation",
        ),
        (
            "Would you rather have one wild adventure or several smaller adventures?",
            "🔥 One wild one",
            "😈 Several",
        ),
    ],
}


# ==========================================================
# NEVER HAVE I EVER
# ==========================================================

NEVER_HAVE_I_EVER = {

    "mild": [
        "Never have I ever gone on a date just because I liked someone's smile.",
        "Never have I ever had a crush on someone I met online.",
        "Never have I ever flirted with someone I just met.",
        "Never have I ever stayed up all night talking to someone.",
        "Never have I ever sent a risky text and immediately regretted it.",
        "Never have I ever had a secret crush.",
        "Never have I ever gone on a spontaneous date.",
        "Never have I ever pretended not to be interested when I actually was.",
        "Never have I ever fallen for someone's personality first.",
        "Never have I ever flirted with someone across the room.",
    ],

    "spicy": [
        "Never have I ever sent a flirty picture.",
        "Never have I ever had chemistry with someone I wasn't expecting.",
        "Never have I ever flirted with someone at a party.",
        "Never have I ever had a secret fantasy about someone.",
        "Never have I ever intentionally teased someone.",
        "Never have I ever stayed up late having an extremely flirty conversation.",
        "Never have I ever kissed someone I met that same night.",
        "Never have I ever had a date turn much more interesting than expected.",
        "Never have I ever flirted with someone just to see their reaction.",
        "Never have I ever had a crush on someone I probably shouldn't have.",
    ],

    "extreme": [
        "Never have I ever explored a kink with a consenting partner.",
        "Never have I ever tried something adventurous because my partner wanted to.",
        "Never have I ever had a fantasy come true.",
        "Never have I ever had an unexpected connection become something more.",
        "Never have I ever discussed a fantasy with a partner that I was nervous to reveal.",
        "Never have I ever tried something completely outside my comfort zone with trusted adults.",
        "Never have I ever had a date turn into an unforgettable adventure.",
        "Never have I ever explored something I once thought I would never try.",
        "Never have I ever had chemistry with someone immediately.",
        "Never have I ever kept an adventurous experience completely private.",
    ],
}


# ==========================================================
# MOST LIKELY TO
# ==========================================================

MOST_LIKELY = {

    "mild": [
        "Who is most likely to make the first move?",
        "Who is most likely to plan the perfect date?",
        "Who is most likely to flirt without realizing it?",
        "Who is most likely to stay up all night talking?",
        "Who is most likely to make everyone laugh?",
        "Who is most likely to disappear on a spontaneous adventure?",
        "Who is most likely to have the best pickup line?",
        "Who is most likely to make a new friend tonight?",
        "Who is most likely to fall for someone's personality?",
        "Who is most likely to organize the next group outing?",
    ],

    "spicy": [
        "Who is most likely to make the first flirty move?",
        "Who is most likely to make someone blush?",
        "Who is most likely to send a risky text?",
        "Who is most likely to plan a spicy date?",
        "Who is most likely to be the biggest tease?",
        "Who is most likely to flirt with someone across the room?",
        "Who is most likely to have the wildest dating story?",
        "Who is most likely to turn a normal date into an adventure?",
        "Who is most likely to have someone crushing on them secretly?",
        "Who is most likely to make the first move at a party?",
    ],

    "extreme": [
        "Who is most likely to suggest a completely spontaneous adventure?",
        "Who is most likely to have the wildest bucket list?",
        "Who is most likely to try something new with a trusted partner?",
        "Who is most likely to plan an unforgettable adults-only night?",
        "Who is most likely to reveal a surprising fantasy?",
        "Who is most likely to say YES to an adventure?",
        "Who is most likely to have the most interesting dating story?",
        "Who is most likely to surprise everyone with their hidden adventurous side?",
        "Who is most likely to organize a group adventure?",
        "Who is most likely to turn a quiet night into an unforgettable one?",
    ],
}


# ==========================================================
# THIS OR THAT
# ==========================================================

THIS_OR_THAT = {

    "mild": [
        ("Beach date", "🏖️", "City date", "🌆"),
        ("Dinner", "🍽️", "Drinks", "🥂"),
        ("Texting", "📱", "Calling", "📞"),
        ("Morning date", "☀️", "Night date", "🌙"),
        ("Netflix", "🎬", "Game night", "🎮"),
        ("Flirting", "😉", "Compliments", "💜"),
        ("Stay home", "🏠", "Go out", "🎉"),
        ("Plan everything", "📋", "Go with the flow", "🎲"),
        ("Sweet", "🍫", "Savory", "🍿"),
        ("Romantic", "❤️", "Playful", "😈"),
    ],

    "spicy": [
        ("Slow burn", "🔥", "Instant chemistry", "⚡"),
        ("Flirting", "😉", "Teasing", "😈"),
        ("Private date", "💜", "Group date", "🔥"),
        ("Pursue", "😈", "Be pursued", "👑"),
        ("Messages", "📱", "Whispers", "🤫"),
        ("Anticipation", "🔥", "Spontaneity", "🎲"),
        ("Romance", "❤️", "Adventure", "🌶️"),
        ("Tease", "😈", "Be teased", "👀"),
        ("Plan it", "📋", "Surprise me", "🎁"),
        ("Chemistry", "🔥", "Connection", "💜"),
    ],

    "extreme": [
        ("New fantasy", "🔥", "Favorite fantasy", "😈"),
        ("Control", "👑", "Give up control", "😈"),
        ("Plan it", "📋", "Go spontaneous", "🎲"),
        ("Private adventure", "💜", "Group adventure", "🔥"),
        ("One wild night", "🔥", "Wild weekend", "🌴"),
        ("Reveal a fantasy", "🤫", "Hear one", "👀"),
        ("Lead", "👑", "Follow", "😈"),
        ("Slow anticipation", "🔥", "Immediate chemistry", "⚡"),
        ("Try something new", "🌶️", "Perfect a favorite", "😈"),
        ("Adventure", "🔥", "Intimacy", "💜"),
    ],
}


# ==========================================================
# HOT SEAT
# ==========================================================

HOT_SEAT = {

    "mild": [
        "What is one thing people notice about you first?",
        "What is your biggest green flag?",
        "What is your favorite way to flirt?",
        "What is your ideal date?",
        "What makes you laugh every time?",
        "What is one thing you are really good at?",
        "What is something people always get wrong about you?",
        "What is your favorite quality in another person?",
        "What is something adventurous you want to try?",
        "What is your biggest dating pet peeve?",
    ],

    "spicy": [
        "What is your biggest turn-on?",
        "What kind of flirting gets your attention?",
        "What makes someone irresistible to you?",
        "What is your favorite kind of teasing?",
        "What is your biggest dating green flag?",
        "What is one fantasy you might explore with the right person?",
        "What makes chemistry happen for you?",
        "What kind of confidence attracts you?",
        "What is the boldest date you would actually agree to?",
        "What instantly makes someone more attractive?",
    ],

    "extreme": [
        "What is one fantasy you have not explored yet?",
        "What is your biggest YES?",
        "What is your biggest NO?",
        "What is something adventurous you would try with trusted consenting adults?",
        "What is one experience on your bucket list?",
        "What kind of chemistry makes you want more?",
        "What is something you would only explore with someone you deeply trust?",
        "What is your wildest acceptable date idea?",
        "What is one thing you have always wanted to be asked?",
        "What is something that instantly makes you curious about someone?",
    ],
}


# ==========================================================
# CONFESSIONS
# ==========================================================

CONFESSIONS = {

    "mild": [
        "Confess something silly you have done on a date.",
        "Confess your biggest dating pet peeve.",
        "Confess your most embarrassing flirting moment.",
        "Confess a harmless secret talent.",
        "Confess the weirdest thing you find attractive.",
        "Confess whether you usually make the first move.",
        "Confess your biggest green flag.",
        "Confess something you are secretly proud of.",
        "Confess your worst pickup line experience.",
        "Confess one thing people misunderstand about you.",
    ],

    "spicy": [
        "Confess something that instantly gets your attention.",
        "Confess your biggest turn-on.",
        "Confess your favorite way to flirt.",
        "Confess your favorite type of teasing.",
        "Confess a fantasy you might explore with the right consenting adults.",
        "Confess your boldest dating move.",
        "Confess something that makes you immediately curious about someone.",
        "Confess your favorite kind of chemistry.",
        "Confess whether you prefer pursuing or being pursued.",
        "Confess something you find unexpectedly attractive.",
    ],

    "extreme": [
        "Confess one fantasy that is still on your bucket list.",
        "Confess your biggest YES.",
        "Confess your biggest MAYBE.",
        "Confess one thing that is completely off limits.",
        "Confess something adventurous you would try with someone you trust.",
        "Confess the boldest experience you would consider.",
        "Confess a fantasy you have discussed with a partner.",
        "Confess something that would instantly make you curious about someone.",
        "Confess the most adventurous date you would agree to.",
        "Confess something you would only explore with explicit mutual consent.",
    ],
}


# ==========================================================
# COMPLIMENT BATTLE
# ==========================================================

COMPLIMENT_BATTLE = [
    "Give someone a genuine compliment about their personality.",
    "Compliment someone's energy.",
    "Tell someone what makes them stand out.",
    "Give someone a creative compliment.",
    "Compliment someone's sense of humor.",
    "Tell someone what you appreciate about their vibe.",
    "Give someone a respectful flirty compliment.",
    "Tell someone why they seem fun to be around.",
    "Compliment someone's confidence.",
    "Give someone a compliment that would make them smile.",
    "Tell someone something positive you noticed about them.",
    "Give someone your best wholesome pickup-line compliment.",
]


# ==========================================================
# DICE RESULTS
# ==========================================================

DICE_RESULTS = [
    "🎲 You rolled a 1 — Keep it simple.",
    "🎲 You rolled a 2 — Pick someone to answer a question.",
    "🎲 You rolled a 3 — Give someone a compliment.",
    "🎲 You rolled a 4 — Choose Truth or Dare.",
    "🎲 You rolled a 5 — Ask the group a question.",
    "🎲 You rolled a 6 — You're feeling lucky! 🔥",
]


# ==========================================================
# COIN FLIP
# ==========================================================

COIN_RESULTS = [
    "🪙 HEADS!",
    "🪙 TAILS!",
]


# ==========================================================
# RANDOM HELPERS
# ==========================================================

def random_truth(level="mild"):
    """
    Return a random Truth question.
    """

    questions = HOT_SEAT.get(
        level,
        HOT_SEAT["mild"],
    )

    return random.choice(questions)


def random_would_you_rather(level="mild"):
    """
    Return a random Would You Rather entry.

    Returns:
        tuple(question, option_a, option_b)
    """

    questions = WOULD_YOU_RATHER.get(
        level,
        WOULD_YOU_RATHER["mild"],
    )

    return random.choice(questions)


def random_never_have_i_ever(level="mild"):
    """
    Return a random Never Have I Ever statement.
    """

    questions = NEVER_HAVE_I_EVER.get(
        level,
        NEVER_HAVE_I_EVER["mild"],
    )

    return random.choice(questions)


def random_most_likely(level="mild"):
    """
    Return a random Most Likely To question.
    """

    questions = MOST_LIKELY.get(
        level,
        MOST_LIKELY["mild"],
    )

    return random.choice(questions)


def random_this_or_that(level="mild"):
    """
    Return a random This or That entry.

    Returns:
        tuple(option_a, emoji_a, option_b, emoji_b)
    """

    choices = THIS_OR_THAT.get(
        level,
        THIS_OR_THAT["mild"],
    )

    return random.choice(choices)


def random_hot_seat(level="mild"):
    """
    Return a random Hot Seat question.
    """

    questions = HOT_SEAT.get(
        level,
        HOT_SEAT["mild"],
    )

    return random.choice(questions)


def random_confession(level="mild"):
    """
    Return a random confession prompt.
    """

    questions = CONFESSIONS.get(
        level,
        CONFESSIONS["mild"],
    )

    return random.choice(questions)


def random_compliment():
    """
    Return a random compliment challenge.
    """

    return random.choice(
        COMPLIMENT_BATTLE
    )


def random_dice_result():
    """
    Return a random dice result.
    """

    return random.choice(
        DICE_RESULTS
    )


def random_coin_result():
    """
    Return Heads or Tails.
    """

    return random.choice(
        COIN_RESULTS
    )


# ==========================================================
# END game_data.py
# ==========================================================
