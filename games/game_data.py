# ==========================================================
# Melanated AZ Bot
# games/game_data.py
#
# CENTRAL GAME CONTENT
#
# This file contains the content used by the Games system.
#
# IMPORTANT:
#   - No Telegram imports
#   - No imports from games.py
#   - No imports from individual game files
#   - Safe to expand with additional questions/challenges
# ==========================================================


# ==========================================================
# GAME DEFINITIONS
# ==========================================================

GAME_DEFINITIONS = {

    # ======================================================
    # TRIVIA
    # ======================================================

    "trivia": {
        "name": "🧠 Trivia",
        "description": "Test your knowledge.",
        "type": "trivia",
        "enabled": True,
    },

    # ======================================================
    # WOULD YOU RATHER
    # ======================================================

    "would_you_rather": {
        "name": "🤔 Would You Rather",
        "description": "Pick between two choices.",
        "type": "would_you_rather",
        "enabled": True,
    },

    # ======================================================
    # TRUTH OR DARE
    # ======================================================

    "truth_dare": {
        "name": "🔥 Truth or Dare",
        "description": "Truths, dares, and PASS.",
        "type": "truth_dare",
        "enabled": True,
    },

    # ======================================================
    # NEVER HAVE I EVER
    # ======================================================

    "never_have_i_ever": {
        "name": "🙅 Never Have I Ever",
        "description": "Confess or deny.",
        "type": "never_have_i_ever",
        "enabled": True,
    },

    # ======================================================
    # MOST LIKELY TO
    # ======================================================

    "most_likely": {
        "name": "👀 Most Likely To",
        "description": "Choose who fits the statement.",
        "type": "most_likely",
        "enabled": True,
    },

    # ======================================================
    # THIS OR THAT
    # ======================================================

    "this_or_that": {
        "name": "⚡ This or That",
        "description": "Choose your favorite.",
        "type": "this_or_that",
        "enabled": True,
    },

    # ======================================================
    # HOT SEAT
    # ======================================================

    "hot_seat": {
        "name": "🔥 Hot Seat",
        "description": "Answer the question or PASS.",
        "type": "hot_seat",
        "enabled": True,
    },

    # ======================================================
    # GUESSING GAMES
    # ======================================================

    "guessing": {
        "name": "🎯 Guessing Games",
        "description": "Make your best guess.",
        "type": "guessing",
        "enabled": True,
    },

    # ======================================================
    # WORD GAMES
    # ======================================================

    "word_games": {
        "name": "🔤 Word Games",
        "description": "Challenge your vocabulary.",
        "type": "word_games",
        "enabled": True,
    },

    # ======================================================
    # PARTY GAMES
    # ======================================================

    "party_games": {
        "name": "🎉 Party Games",
        "description": "Quick games for the group.",
        "type": "party_games",
        "enabled": True,
    },
}


# ==========================================================
# NEVER HAVE I EVER
# ==========================================================

NEVER_HAVE_I_EVER = {

    "mild": [

        "Never have I ever stayed up all night talking to someone.",
        "Never have I ever had a crush on someone I shouldn't have.",
        "Never have I ever lied about being busy to avoid a date.",
        "Never have I ever sent a message and immediately regretted it.",
        "Never have I ever flirted with someone just for fun.",
        "Never have I ever fallen for someone's personality before their looks.",
        "Never have I ever had a crush on a friend.",
        "Never have I ever gone on a date without knowing what to expect.",
        "Never have I ever pretended not to notice someone flirting with me.",
        "Never have I ever made the first move.",
        "Never have I ever re-read an old conversation.",
        "Never have I ever gotten nervous before meeting someone.",
        "Never have I ever had chemistry with someone I didn't expect.",
        "Never have I ever had a secret crush.",
        "Never have I ever changed my outfit because someone I liked was going to be there.",
    ],

    "spicy": [

        "Never have I ever flirted with someone I met online.",
        "Never have I ever had chemistry with someone I met at a party.",
        "Never have I ever sent a flirty picture.",
        "Never have I ever kissed someone on a first date.",
        "Never have I ever been attracted to someone completely unexpected.",
        "Never have I ever had a crush on someone who was taken.",
        "Never have I ever intentionally made someone jealous.",
        "Never have I ever had a secret admirer.",
        "Never have I ever flirted with someone while my partner knew about it.",
        "Never have I ever gone on a date that turned much more adventurous than expected.",
        "Never have I ever stayed up all night with someone because the chemistry was too good.",
        "Never have I ever had a fantasy about someone I knew.",
        "Never have I ever exchanged flirty messages late at night.",
        "Never have I ever been tempted to make a bold first move.",
        "Never have I ever explored a new experience because someone made me curious.",
    ],

    "extreme": [

        "Never have I ever explored a new kink with a consenting partner.",
        "Never have I ever had a fantasy involving more than one person.",
        "Never have I ever attended an adults-only event.",
        "Never have I ever had a spontaneous adult adventure.",
        "Never have I ever explored something outside my normal comfort zone.",
        "Never have I ever had chemistry with someone I met through an adult community.",
        "Never have I ever discussed a fantasy with a partner that I wanted to try.",
        "Never have I ever considered an experience with another couple.",
        "Never have I ever considered an experience with a single person outside my usual dating style.",
        "Never have I ever had an adventure that I would never tell my coworkers about.",
        "Never have I ever tried something simply because my partner was curious.",
        "Never have I ever had a fantasy that stayed on my bucket list for years.",
        "Never have I ever had an unexpectedly intense connection with someone.",
        "Never have I ever said YES to an adventure before knowing exactly how it would go.",
        "Never have I ever had an experience that completely changed what I thought I liked.",
    ],
}


# ==========================================================
# MOST LIKELY TO
# ==========================================================

MOST_LIKELY = {

    "mild": [

        "Who is most likely to make the first move?",
        "Who is most likely to plan the perfect date?",
        "Who is most likely to stay up talking all night?",
        "Who is most likely to flirt without realizing it?",
        "Who is most likely to make everyone laugh?",
        "Who is most likely to travel on a last-minute adventure?",
        "Who is most likely to fall for someone's personality?",
        "Who is most likely to send the first message?",
        "Who is most likely to organize the group?",
        "Who is most likely to have a secret crush?",
        "Who is most likely to give the best relationship advice?",
        "Who is most likely to break the ice with a stranger?",
        "Who is most likely to turn a casual night into an adventure?",
        "Who is most likely to have the best playlist?",
        "Who is most likely to make a bold decision?",
    ],

    "spicy": [

        "Who is most likely to send the first flirty message?",
        "Who is most likely to make someone blush?",
        "Who is most likely to plan an adults-only date?",
        "Who is most likely to start flirting first?",
        "Who is most likely to have the wildest bucket list?",
        "Who is most likely to talk their way into an adventure?",
        "Who is most likely to have a secret fantasy?",
        "Who is most likely to make the first bold move?",
        "Who is most likely to enjoy being teased?",
        "Who is most likely to be the biggest flirt in the room?",
        "Who is most likely to have chemistry with someone unexpected?",
        "Who is most likely to convince everyone to stay out later?",
        "Who is most likely to suggest trying something new?",
        "Who is most likely to make an unforgettable first impression?",
        "Who is most likely to turn flirting into a real connection?",
    ],

    "extreme": [

        "Who is most likely to suggest the wildest adventure?",
        "Who is most likely to have the boldest fantasy?",
        "Who is most likely to try something completely outside their comfort zone?",
        "Who is most likely to suggest an adults-only adventure?",
        "Who is most likely to have the longest bucket list?",
        "Who is most likely to make a very bold first move?",
        "Who is most likely to turn a casual conversation into serious chemistry?",
        "Who is most likely to suggest a new experience to their partner?",
        "Who is most likely to say YES to an unexpected adventure?",
        "Who is most likely to have the most interesting secret?",
        "Who is most likely to surprise everyone with their answer?",
        "Who is most likely to flirt their way into an adventure?",
        "Who is most likely to have a fantasy they have never told anyone?",
        "Who is most likely to make someone completely speechless?",
        "Who is most likely to suggest something adventurous but respectful?",
    ],
}


# ==========================================================
# THIS OR THAT
# ==========================================================

THIS_OR_THAT = {

    "mild": [

        ("Coffee", "Tea"),
        ("Beach", "Mountains"),
        ("Night out", "Night in"),
        ("Texting", "Calling"),
        ("Dinner date", "Activity date"),
        ("Morning person", "Night owl"),
        ("Sweet", "Savory"),
        ("Movies", "Music"),
        ("Road trip", "Flying"),
        ("Summer", "Winter"),
        ("Flirting", "Being flirted with"),
        ("Plan everything", "Go with the flow"),
        ("First move", "Being pursued"),
        ("Big party", "Small gathering"),
        ("Romantic date", "Adventurous date"),
    ],

    "spicy": [

        ("Slow flirting", "Bold flirting"),
        ("Private date", "Night out"),
        ("Being pursued", "Doing the pursuing"),
        ("Teasing", "Being teased"),
        ("Romantic chemistry", "Physical chemistry"),
        ("Planned adventure", "Spontaneous adventure"),
        ("Long conversation", "Instant chemistry"),
        ("Flirty texts", "Flirty calls"),
        ("One-on-one", "Group adventure"),
        ("Date night", "Adults-only event"),
        ("Sweet talk", "Playful teasing"),
        ("Eye contact", "Whispered compliments"),
        ("Mystery", "Knowing exactly what is coming"),
        ("Slow burn", "Instant spark"),
        ("Confident flirt", "Shy flirt"),
    ],

    "extreme": [

        ("Slow burn", "Instant fire"),
        ("Plan everything", "Completely spontaneous"),
        ("One-on-one adventure", "Group adventure"),
        ("Romantic fantasy", "Kinky fantasy"),
        ("Being teased", "Doing the teasing"),
        ("Private getaway", "Adults-only event"),
        ("Known fantasy", "New experiment"),
        ("Comfort zone", "New territory"),
        ("Long anticipation", "Immediate chemistry"),
        ("Bold first move", "Let them make the first move"),
        ("Trusted partner", "Trusted new connection"),
        ("Predictable adventure", "Unexpected adventure"),
        ("Talk about it first", "See where the night goes"),
        ("Romance first", "Chemistry first"),
        ("Fantasy conversation", "Fantasy experience"),
    ],
}


# ==========================================================
# HOT SEAT
# ==========================================================

HOT_SEAT = {

    "mild": [

        "What is one thing you wish people noticed about you sooner?",
        "What is your biggest green flag?",
        "What is your biggest dating pet peeve?",
        "What makes you feel appreciated?",
        "What is your favorite kind of date?",
        "What is something you are surprisingly good at?",
        "What is one thing you would love to learn?",
        "What is your biggest turn-off in conversation?",
        "What makes someone memorable to you?",
        "What is something you value most in a connection?",
        "What is your favorite way to spend a free evening?",
        "What is something you would never compromise on?",
    ],

    "spicy": [

        "What is your biggest turn-on?",
        "What kind of flirting gets your attention immediately?",
        "What is something that instantly creates chemistry for you?",
        "What is your favorite way to build anticipation?",
        "What kind of confidence do you find attractive?",
        "What is something adventurous you would like to try?",
        "What is your favorite kind of teasing?",
        "What is something that makes you feel desired?",
        "What is your favorite type of adults-only date?",
        "What kind of energy makes you curious about someone?",
        "What is a fantasy you would consider discussing with the right person?",
        "What is one boundary you always communicate?",
    ],

    "extreme": [

        "What is one fantasy you would consider exploring with trusted consenting adults?",
        "What is your biggest YES?",
        "What is your biggest MAYBE?",
        "What is your absolute HARD NO?",
        "What is one experience that is still on your bucket list?",
        "What is the boldest adventure you would consider?",
        "What is one thing you would only explore with someone you deeply trust?",
        "What kind of situation creates the strongest chemistry for you?",
        "What is one fantasy you have never acted on?",
        "What would make you immediately say YES to an adventure?",
        "What would make you immediately walk away?",
        "What is something adventurous you want to experience someday?",
    ],
}


# ==========================================================
# GUESSING GAMES
# ==========================================================

GUESSING_GAMES = {

    "easy": [

        {
            "type": "number",
            "question": "Guess a number between 1 and 10.",
            "answer": None,
            "range": (1, 10),
        },

        {
            "type": "number",
            "question": "Guess a number between 1 and 20.",
            "answer": None,
            "range": (1, 20),
        },

        {
            "type": "number",
            "question": "Guess a number between 1 and 50.",
            "answer": None,
            "range": (1, 50),
        },

    ],

    "medium": [

        {
            "type": "number",
            "question": "Guess a number between 1 and 100.",
            "answer": None,
            "range": (1, 100),
        },

        {
            "type": "number",
            "question": "Guess a number between 1 and 250.",
            "answer": None,
            "range": (1, 250),
        },

    ],

    "hard": [

        {
            "type": "number",
            "question": "Guess a number between 1 and 500.",
            "answer": None,
            "range": (1, 500),
        },

        {
            "type": "number",
            "question": "Guess a number between 1 and 1000.",
            "answer": None,
            "range": (1, 1000),
        },

    ],
}


# ==========================================================
# WORD GAMES
# ==========================================================

WORD_GAMES = {

    "easy": [

        {
            "word": "MELANATED",
            "scrambled": "LAMETENAD",
        },

        {
            "word": "COMMUNITY",
            "scrambled": "MUNYOTMIC",
        },

        {
            "word": "FRIENDS",
            "scrambled": "SFRIEND",
        },

        {
            "word": "ADVENTURE",
            "scrambled": "TURVENADE",
        },

        {
            "word": "MUSIC",
            "scrambled": "CUSIM",
        },

    ],

    "medium": [

        {
            "word": "CONNECTION",
            "scrambled": "NECTONCION",
        },

        {
            "word": "CONFIDENCE",
            "scrambled": "FIDENCENCO",
        },

        {
            "word": "RELATIONSHIP",
            "scrambled": "SHIPRELATION",
        },

        {
            "word": "ADVENTUROUS",
            "scrambled": "VENTUROUSAD",
        },

        {
            "word": "CHEMISTRY",
            "scrambled": "TRYCHEMIS",
        },

    ],

    "hard": [

        {
            "word": "AUTHENTICITY",
            "scrambled": "THENTICITYAU",
        },

        {
            "word": "COMMUNICATION",
            "scrambled": "MUNICATIONCOM",
        },

        {
            "word": "CONSENT",
            "scrambled": "SENTCON",
        },

        {
            "word": "BOUNDARIES",
            "scrambled": "DARIESBOUN",
        },

        {
            "word": "COMPATIBILITY",
            "scrambled": "PATIBILITYCOM",
        },

    ],
}


# ==========================================================
# PARTY GAMES
# ==========================================================

PARTY_GAMES = {

    "mild": [

        "Everyone describe their perfect weekend in three words.",
        "Everyone name one song they could listen to all night.",
        "Everyone give the person above them a compliment.",
        "Everyone share one place they would love to visit.",
        "Everyone reveal their favorite comfort food.",
        "Everyone describe their personality using three emojis.",
        "Everyone share one thing that always makes them laugh.",
        "Everyone say whether they prefer staying in or going out.",
        "Everyone name their favorite movie.",
        "Everyone share one thing on their bucket list.",
    ],

    "spicy": [

        "Everyone share their biggest dating green flag.",
        "Everyone describe their ideal adults-only date.",
        "Everyone reveal their favorite kind of flirting.",
        "Everyone share their biggest turn-on.",
        "Everyone say whether they prefer teasing or being teased.",
        "Everyone describe their perfect chemistry in three words.",
        "Everyone share one adventurous experience they would consider.",
        "Everyone reveal whether they prefer pursuing or being pursued.",
        "Everyone describe their ideal date-night atmosphere.",
        "Everyone share one thing that instantly makes someone attractive.",
    ],

    "extreme": [

        "Everyone share their biggest YES, MAYBE, or NO.",
        "Everyone describe one adventure they would consider with trusted consenting adults.",
        "Everyone reveal one fantasy they would consider discussing with a partner.",
        "Everyone describe their perfect adventurous night.",
        "Everyone share one experience that is still on their bucket list.",
        "Everyone name one boundary that is important to them.",
        "Everyone share one thing that instantly creates chemistry.",
        "Everyone describe their ideal adults-only adventure.",
        "Everyone reveal whether they prefer planning or spontaneous adventures.",
        "Everyone share one bold experience they might consider someday.",
    ],
}


# ==========================================================
# CATEGORY HELPERS
# ==========================================================

def get_game_definition(game_id):

    return GAME_DEFINITIONS.get(
        game_id
    )


def get_enabled_games():

    return {
        game_id: definition
        for game_id, definition
        in GAME_DEFINITIONS.items()
        if definition.get(
            "enabled",
            False,
        )
    }


def get_game_name(game_id):

    definition = get_game_definition(
        game_id
    )

    if not definition:

        return game_id

    return definition.get(
        "name",
        game_id,
    )


# ==========================================================
# CONTENT HELPERS
# ==========================================================

def get_never_have_i_ever(level):

    return NEVER_HAVE_I_EVER.get(
        level,
        NEVER_HAVE_I_EVER["mild"],
    )


def get_most_likely(level):

    return MOST_LIKELY.get(
        level,
        MOST_LIKELY["mild"],
    )


def get_this_or_that(level):

    return THIS_OR_THAT.get(
        level,
        THIS_OR_THAT["mild"],
    )


def get_hot_seat(level):

    return HOT_SEAT.get(
        level,
        HOT_SEAT["mild"],
    )


def get_guessing_games(level):

    return GUESSING_GAMES.get(
        level,
        GUESSING_GAMES["easy"],
    )


def get_word_games(level):

    return WORD_GAMES.get(
        level,
        WORD_GAMES["easy"],
    )


def get_party_games(level):

    return PARTY_GAMES.get(
        level,
        PARTY_GAMES["mild"],
    )


# ==========================================================
# END game_data.py
# ==========================================================
