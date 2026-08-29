# ==========================================================
# Melanated AZ Bot
# games/game_data.py
#
# Game categories, game definitions, and prompts.
#
# IMPORTANT:
# This file contains GAME CONTENT only.
# The game engine and Telegram handlers are separate.
#
# PASS is always allowed.
# Keep all interactions respectful and consent-focused.
# ==========================================================


# ==========================================================
# GAME CATEGORIES
# ==========================================================

GAME_CATEGORIES = {

    "adult": "🔥 Adult & Spicy",

    "couples": "💜 Couples",

    "party": "😈 Party Games",

    "lifestyle": "🦄 Lifestyle",

    "icebreakers": "😂 Icebreakers",
}


# ==========================================================
# GAMES
#
# Each game has:
#   name
#   description
#
# The key is used internally by the game engine.
# ==========================================================

GAMES = {

    # ======================================================
    # ADULT & SPICY
    # ======================================================

    "adult": {

        "truth_dare": {
            "name": "🔥 Truth or Dare",
            "description": (
                "Choose Truth or Dare with different "
                "levels of intensity."
            ),
        },

        "would_you_rather": {
            "name": "🌶️ Would You Rather",
            "description": (
                "Choose between two fun, flirty, "
                "or adventurous options."
            ),
        },

        "never_have_i_ever": {
            "name": "😈 Never Have I Ever",
            "description": (
                "Reveal whether you have ever done "
                "something from the prompt."
            ),
        },

        "hot_seat": {
            "name": "🔥 Hot Seat",
            "description": (
                "Answer a bold question while you're "
                "in the hot seat."
            ),
        },
    },


    # ======================================================
    # COUPLES
    # ======================================================

    "couples": {

        "couples_challenge": {
            "name": "💜 Couple's Challenge",
            "description": (
                "Fun challenges designed for couples."
            ),
        },

        "know_your_partner": {
            "name": "🫶 Know Your Partner",
            "description": (
                "See how well you really know your partner."
            ),
        },

        "couples_would_you_rather": {
            "name": "💜 Couple's Would You Rather",
            "description": (
                "Couples choose between fun scenarios."
            ),
        },
    },


    # ======================================================
    # PARTY GAMES
    # ======================================================

    "party": {

        "most_likely": {
            "name": "😂 Most Likely To",
            "description": (
                "Choose the person in the group "
                "most likely to fit the prompt."
            ),
        },

        "two_truths": {
            "name": "🎭 Two Truths & A Lie",
            "description": (
                "Give the group three statements "
                "and see if they can find the lie."
            ),
        },

        "pick_a_player": {
            "name": "🎯 Pick A Player",
            "description": (
                "Choose another player for a fun challenge."
            ),
        },

        "finish_sentence": {
            "name": "🗣️ Finish The Sentence",
            "description": (
                "Complete a random sentence "
                "with your own answer."
            ),
        },
    },


    # ======================================================
    # LIFESTYLE
    # ======================================================

    "lifestyle": {

        "yes_maybe_no": {
            "name": "🦄 Yes / Maybe / No",
            "description": (
                "Discuss different experiences "
                "using Yes, Maybe, or No."
            ),
        },

        "kink_quiz": {
            "name": "🦄 Kink Quiz",
            "description": (
                "Explore interests, communication, "
                "boundaries, and preferences."
            ),
        },

        "lifestyle_would_you_rather": {
            "name": "🌶️ Lifestyle Would You Rather",
            "description": (
                "Choose between different "
                "lifestyle scenarios."
            ),
        },
    },


    # ======================================================
    # ICEBREAKERS
    # ======================================================

    "icebreakers": {

        "random_question": {
            "name": "💬 Random Question",
            "description": (
                "A random question to get "
                "the conversation started."
            ),
        },

        "this_or_that": {
            "name": "⚡ This or That",
            "description": (
                "Quick-fire choices. "
                "Pick one."
            ),
        },

        "compliment_challenge": {
            "name": "💜 Compliment Challenge",
            "description": (
                "Give another member a genuine "
                "and respectful compliment."
            ),
        },

        "rapid_fire": {
            "name": "⚡ Rapid Fire",
            "description": (
                "Answer quick questions "
                "without overthinking."
            ),
        },
    },
}


# ==========================================================
# GAME PROMPTS
#
# These are organized by GAME KEY.
#
# The engine randomly selects from the appropriate list.
# ==========================================================

PROMPTS = {


    # ======================================================
    # WOULD YOU RATHER
    # ======================================================

    "would_you_rather": [

        "Would you rather plan the adventure or be surprised?",

        "Would you rather have instant chemistry or build it slowly?",

        "Would you rather flirt through messages or face to face?",

        "Would you rather go on a spontaneous date or a carefully planned one?",

        "Would you rather meet a fun single or an adventurous couple?",

        "Would you rather be pursued or do the pursuing?",

        "Would you rather have a romantic night in or a wild night out?",

        "Would you rather make the first move or have someone approach you?",

        "Would you rather travel with your partner or stay home together?",

        "Would you rather have great conversation or instant physical chemistry?",
    ],


    # ======================================================
    # NEVER HAVE I EVER
    # ======================================================

    "never_have_i_ever": [

        "Never have I ever flirted with someone I just met.",

        "Never have I ever gone on a completely spontaneous date.",

        "Never have I ever had unexpected chemistry with someone.",

        "Never have I ever changed my plans because the vibe was too good.",

        "Never have I ever stayed up all night talking to someone new.",

        "Never have I ever tried something adventurous because my partner suggested it.",

        "Never have I ever flirted with someone through a dating app.",

        "Never have I ever gone somewhere without knowing how the night would end.",

        "Never have I ever developed a crush on someone I didn't expect to.",

        "Never have I ever made the first move on someone.",
    ],


    # ======================================================
    # HOT SEAT
    # ======================================================

    "hot_seat": [

        "What instantly makes someone more attractive to you?",

        "What is your biggest green flag?",

        "What kind of chemistry catches your attention?",

        "What is something adventurous you would like to try someday?",

        "What is your biggest YES when exploring with consenting adults?",

        "What is one boundary you communicate upfront?",

        "What kind of flirting gets your attention fastest?",

        "What makes someone unforgettable to you?",

        "What type of confidence do you find attractive?",

        "What is something you find unexpectedly attractive?",

        "What makes you feel comfortable around someone new?",

        "What is one thing that instantly kills the vibe for you?",
    ],


    # ======================================================
    # COUPLE'S CHALLENGE
    # ======================================================

    "couples_challenge": [

        "Each partner gives the other one genuine compliment.",

        "Describe your partner in three words.",

        "Tell the group one thing you appreciate about your partner.",

        "Choose a song that represents your relationship.",

        "Share one adventure you would like to take together.",

        "Give your partner a playful nickname for the next round.",

        "Tell your partner one thing they do that always makes you smile.",

        "Describe your perfect date together.",

        "Tell your partner one thing you would like to do together someday.",

        "Each partner says one thing they admire about the other.",
    ],


    # ======================================================
    # KNOW YOUR PARTNER
    # ======================================================

    "know_your_partner": [

        "What is your partner's favorite way to receive attention?",

        "What is your partner's ideal date?",

        "What is one thing your partner considers a hard boundary?",

        "What makes your partner feel appreciated?",

        "What is your partner's favorite way to relax?",

        "What adventure would your partner most likely say yes to?",

        "What is your partner's favorite way to flirt?",

        "What is one thing your partner finds attractive?",

        "What would your partner choose for a perfect night out?",

        "What is something your partner has always wanted to try?",
    ],


    # ======================================================
    # COUPLE'S WOULD YOU RATHER
    # ======================================================

    "couples_would_you_rather": [

        "Would you rather plan a surprise date or receive one?",

        "Would you rather travel together or have a stay-at-home adventure?",

        "Would you rather try something new together or revisit a favorite experience?",

        "Would you rather have a quiet romantic night or a social night out?",

        "Would you rather have a weekend getaway or a surprise date night?",

        "Would you rather cook together or go out for dinner?",

        "Would you rather dance together or watch a movie together?",

        "Would you rather plan everything or completely wing it?",
    ],


    # ======================================================
    # MOST LIKELY TO
    # ======================================================

    "most_likely": [

        "Who is most likely to make the first move?",

        "Who is most likely to plan a spontaneous adventure?",

        "Who is most likely to flirt first?",

        "Who is most likely to talk to someone new?",

        "Who is most likely to suggest a road trip?",

        "Who is most likely to stay up all night talking?",

        "Who is most likely to try something completely new?",

        "Who is most likely to make everyone laugh?",

        "Who is most likely to organize the next group event?",

        "Who is most likely to disappear on an adventure and come back with a story?",
    ],


    # ======================================================
    # TWO TRUTHS & A LIE
    # ======================================================

    "two_truths": [

        "Post two truths and one lie about yourself. Let the group guess.",

        "Share three facts about yourself. Make one of them a lie.",

        "Tell the group three things you've done. One must be made up.",

        "Share three unusual facts about yourself and let everyone vote on the lie.",

        "Post three statements about yourself. Don't reveal the lie until everyone guesses.",
    ],


    # ======================================================
    # PICK A PLAYER
    # ======================================================

    "pick_a_player": [

        "Pick a player and give them a genuine compliment.",

        "Pick a player and ask them a fun question.",

        "Pick a player and tell them what caught your attention about their vibe.",

        "Pick a player to choose the next game.",

        "Pick a player and ask them what their perfect date looks like.",

        "Pick a player and give them your best respectful pickup line.",

        "Pick a player and ask them what their biggest green flag is.",

        "Pick a player and tell them they have good energy.",
    ],


    # ======================================================
    # FINISH THE SENTENCE
    # ======================================================

    "finish_sentence": [

        "The quickest way to win me over is ______.",

        "My perfect date starts with ______.",

        "One thing I will always say yes to is ______.",

        "A huge green flag is ______.",

        "The best kind of chemistry is ______.",

        "My ideal weekend would include ______.",

        "The first thing I notice about someone is ______.",

        "My favorite way to flirt is ______.",

        "The best conversation starts with ______.",

        "One adventure I want to experience is ______.",
    ],


    # ======================================================
    # YES / MAYBE / NO
    # ======================================================

    "yes_maybe_no": [

        "Spontaneous dates",

        "Meeting another couple",

        "Meeting a single",

        "Flirty texting",

        "Trying a new social event",

        "Planning an adventure with friends",

        "Discussing fantasies with a trusted partner",

        "Trying something new with clear boundaries",

        "Going to an adults-only social event",

        "Meeting someone new through mutual friends",

        "Taking a spontaneous weekend trip",

        "Trying a new form of flirting",
    ],


    # ======================================================
    # KINK QUIZ
    # ======================================================

    "kink_quiz": [

        "How important is communication before trying something new?",

        "How important is aftercare to you?",

        "Do you prefer planning or spontaneity?",

        "How comfortable are you discussing boundaries upfront?",

        "How important is trust before exploring?",

        "Do you prefer leading, following, switching, or simply observing?",

        "How important is checking in during an experience?",

        "Would you rather explore slowly or jump into something new?",

        "How important is discussing expectations beforehand?",

        "What makes an experience feel safe and comfortable to you?",
    ],


    # ======================================================
    # LIFESTYLE WOULD YOU RATHER
    # ======================================================

    "lifestyle_would_you_rather": [

        "Would you rather attend a private party or a social mixer?",

        "Would you rather meet people through friends or at an event?",

        "Would you rather have a planned experience or spontaneous chemistry?",

        "Would you rather explore one new thing deeply or several things casually?",

        "Would you rather attend a small intimate gathering or a large social event?",

        "Would you rather meet someone through conversation or through shared activities?",

        "Would you rather have a relaxed evening or an adventurous night out?",

        "Would you rather know everyone's boundaries beforehand or discuss them naturally?",
    ],


    # ======================================================
    # RANDOM QUESTION
    # ======================================================

    "random_question": [

        "What is something people always notice about you?",

        "What is your favorite way to spend a free evening?",

        "What is one place you want to visit?",

        "What is a hobby you could talk about for hours?",

        "What is your biggest green flag?",

        "What is something you are looking forward to?",

        "What is something that always makes you laugh?",

        "What is one thing you wish more people knew about you?",

        "What is your favorite type of date?",

        "What is one adventure you want to experience?",
    ],


    # ======================================================
    # THIS OR THAT
    # ======================================================

    "this_or_that": [

        "Beach or mountains?",

        "Texting or phone calls?",

        "Night out or night in?",

        "Planned date or spontaneous date?",

        "Flirting or being flirted with?",

        "Road trip or flight?",

        "Music or movies?",

        "Morning person or night owl?",

        "Dinner date or activity date?",

        "Coffee date or drinks and conversation?",

        "Big party or small gathering?",

        "Slow burn or instant chemistry?",
    ],


    # ======================================================
    # COMPLIMENT CHALLENGE
    # ======================================================

    "compliment_challenge": [

        "Compliment someone's personality.",

        "Compliment someone's energy.",

        "Compliment someone's sense of humor.",

        "Compliment someone who made you feel welcome.",

        "Compliment your partner or a friend.",

        "Give someone a respectful compliment without mentioning appearance.",

        "Tell someone they have great energy.",

        "Compliment someone's confidence.",

        "Compliment someone's kindness.",

        "Give someone a creative but respectful compliment.",
    ],


    # ======================================================
    # RAPID FIRE
    # ======================================================

    "rapid_fire": [

        "Coffee or tea?",

        "Sweet or spicy?",

        "Sunrise or sunset?",

        "City or country?",

        "Dancing or karaoke?",

        "Stay in or go out?",

        "Summer or winter?",

        "Flirt first or wait?",

        "Texting or calling?",

        "Beach or pool?",

        "Road trip or vacation flight?",

        "Dinner or dessert?",
    ],
}


# ==========================================================
# TRUTH OR DARE
#
# Truth or Dare remains compatible with the existing
# truth_dare.py system.
#
# These are used by the category-based Games system.
# ==========================================================

TRUTHS = {

    "mild": [

        "What is something people assume about you that is completely wrong?",

        "What is your biggest green flag when meeting someone new?",

        "What is your favorite way to flirt?",

        "What instantly makes someone more attractive to you?",

        "What is something adventurous you would like to try someday?",

        "What is one boundary you always communicate upfront?",

        "What kind of personality catches your attention first?",

        "Would you rather meet another couple or a single for a first experience?",

        "What makes you feel comfortable enough to explore with someone new?",

        "What is your favorite type of date?",

        "What is one thing that makes you feel desired?",

        "Are you more of a tease or the one being teased?",
    ],


    "spicy": [

        "What is something that instantly turns up the chemistry for you?",

        "What is your biggest turn-on when meeting someone new?",

        "What is something adventurous on your kink bucket list?",

        "Have you ever developed unexpected chemistry with someone?",

        "What is your favorite kind of teasing?",

        "What is your favorite way someone can flirt with you?",

        "Would you rather plan an experience or let the night unfold naturally?",

        "What is one thing that instantly makes someone irresistible to you?",

        "What kind of couple catches your attention?",

        "What is something you have always been curious about exploring?",

        "What is your favorite type of adult date night?",

        "What is your favorite way to build anticipation?",
    ],


    "extreme": [

        "What is the boldest experience you would consider trying?",

        "What is one kink you are curious about but have not explored?",

        "What is one fantasy you have discussed with your partner but have not explored yet?",

        "What would make you immediately say YES to an adventure?",

        "What would make you immediately say HARD NO?",

        "Would you rather explore with another couple, a single, or both?",

        "What is something adventurous you would try with the right consenting people?",

        "What is your biggest boundary when exploring?",

        "What is one thing you would love to experience with a partner?",

        "What kind of situation creates the strongest chemistry for you?",

        "What is something you have always wanted to be asked?",

        "What is the most adventurous date you would actually agree to?",
    ],
}


DARES = {

    "mild": [

        "Give someone in the chat a genuine compliment.",

        "Tell the group your favorite way to flirt.",

        "Give someone your best pickup line.",

        "Tell the group whether you are more tease or temptation.",

        "Share your favorite song for setting the mood.",

        "Describe your ideal date in three words.",

        "Tell someone what caught your attention about them.",

        "Give your partner a playful compliment.",

        "Tell the group one of your biggest green flags.",

        "Send someone a 😉 and see if they respond.",
    ],


    "spicy": [

        "Send someone a flirty message that makes your intentions clear.",

        "Give someone your best seductive pickup line.",

        "Tell someone in the group what caught your attention about them.",

        "Invite someone you're interested in to chat privately — if they're interested too.",

        "Send your partner a message designed to make them blush.",

        "Tell the group your ideal couple's night out.",

        "Tell someone what kind of chemistry you are looking for.",

        "Send someone a 😉 and wait for their response.",

        "Tell someone one thing about their vibe that you find attractive.",

        "Share one item from your adult bucket list.",
    ],


    "extreme": [

        "Give someone your most creative seductive pickup line.",

        "Tell someone exactly what made you notice them.",

        "Tell the group about one adventure that is on your bucket list.",

        "Tell the group your biggest YES, biggest MAYBE, and biggest NO.",

        "Tell someone what kind of flirting gets your attention fastest.",

        "Send your partner a message telling them what you find irresistible about them.",

        "Tell the group what makes a couple especially attractive to you.",

        "Tell the group one adventurous experience you would consider with the right consenting people.",

        "Give someone permission to ask you one spicy question. You may still PASS.",

        "Describe your perfect adults-only night out.",
    ],
}


# ==========================================================
# VALIDATION HELPERS
# ==========================================================

def get_categories():

    return GAME_CATEGORIES.copy()


def get_games(category):

    return GAMES.get(
        category,
        {},
    ).copy()


def get_prompts(game_key):

    return PROMPTS.get(
        game_key,
        [],
    ).copy()


def get_truths(level):

    return TRUTHS.get(
        level,
        [],
    ).copy()


def get_dares(level):

    return DARES.get(
        level,
        [],
    ).copy()
