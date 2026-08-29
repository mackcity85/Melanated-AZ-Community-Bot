# ==========================================================
# Melanated AZ Bot
# games/game_data.py
#
# GAME CONTENT DATABASE
#
# This file contains the game definitions and prompts.
#
# IMPORTANT:
#   - No Telegram imports
#   - No bot imports
#   - No admin imports
#   - Content only
# ==========================================================


# ==========================================================
# GAME DEFINITIONS
# ==========================================================

GAME_DEFINITIONS = {

    "truth_dare": {
        "name": "🔥 Truth or Dare",
        "description": "Choose Truth or Dare.",
        "command": "truthdare",
    },

    "would_you_rather": {
        "name": "🤔 Would You Rather",
        "description": "Choose between two choices.",
        "command": "wyr",
    },

    "never_have_i_ever": {
        "name": "🙈 Never Have I Ever",
        "description": "Admit whether you've done it.",
        "command": "never",
    },

    "most_likely": {
        "name": "👀 Most Likely To",
        "description": "Choose who is most likely.",
        "command": "mostlikely",
    },

    "this_or_that": {
        "name": "⚖️ This or That",
        "description": "Pick one of two choices.",
        "command": "thisorthat",
    },

    "hot_seat": {
        "name": "🔥 Hot Seat",
        "description": "One player answers questions.",
        "command": "hotseat",
    },

    "confessions": {
        "name": "🤫 Confessions",
        "description": "Share a confession.",
        "command": "confess",
    },

    "compliment_battle": {
        "name": "💜 Compliment Battle",
        "description": "Give someone a great compliment.",
        "command": "compliment",
    },

    "dice": {
        "name": "🎲 Dice",
        "description": "Roll the dice.",
        "command": "dice",
    },

    "coin_flip": {
        "name": "🪙 Coin Flip",
        "description": "Flip a coin.",
        "command": "coin",
    },
}


# ==========================================================
# WOULD YOU RATHER
# ==========================================================

WOULD_YOU_RATHER = {

    "mild": [

        "Would you rather have a romantic dinner or a fun night out?",
        "Would you rather plan the date or have someone surprise you?",
        "Would you rather stay home or go on an adventure?",
        "Would you rather flirt through messages or in person?",
        "Would you rather receive flowers or your favorite snacks?",
        "Would you rather have amazing chemistry or amazing conversation?",
        "Would you rather travel with someone or have a staycation?",
        "Would you rather make the first move or have someone approach you?",
        "Would you rather dance all night or talk all night?",
        "Would you rather have a spontaneous date or a carefully planned date?",
        "Would you rather meet someone through friends or online?",
        "Would you rather be mysterious or completely open?",
        "Would you rather get compliments or give compliments?",
        "Would you rather have a beach date or a mountain date?",
        "Would you rather watch a movie together or play games together?",
    ],

    "spicy": [

        "Would you rather be the tease or be teased?",
        "Would you rather make the first move or have someone make it?",
        "Would you rather build anticipation slowly or jump straight into chemistry?",
        "Would you rather receive a flirty text or a whispered compliment?",
        "Would you rather have a romantic night or a mischievous night?",
        "Would you rather go on an adults-only vacation or an adults-only date night?",
        "Would you rather flirt all night or spend the night getting to know someone?",
        "Would you rather be pursued or do the pursuing?",
        "Would you rather have incredible chemistry or incredible tension?",
        "Would you rather receive a bold compliment or give one?",
        "Would you rather meet another couple or a single?",
        "Would you rather have a planned adventure or completely spontaneous chemistry?",
        "Would you rather be the one in control or let someone else take the lead?",
        "Would you rather have a playful night or an intense night?",
        "Would you rather share a fantasy or hear someone else's fantasy?",
    ],

    "extreme": [

        "Would you rather reveal your biggest fantasy or your biggest turn-on?",
        "Would you rather explore something completely new or perfect something you already love?",
        "Would you rather be surprised by a partner or plan everything yourself?",
        "Would you rather be the one setting the rules or following them?",
        "Would you rather explore with another couple or a single?",
        "Would you rather have intense chemistry or intense anticipation?",
        "Would you rather share a fantasy publicly or privately?",
        "Would you rather be challenged to try something new or choose the challenge yourself?",
        "Would you rather have a wild adventure or a slow-burn experience?",
        "Would you rather reveal your biggest YES or your biggest MAYBE?",
        "Would you rather let someone else choose the adventure or choose it yourself?",
        "Would you rather have an unforgettable date or an unforgettable night?",
        "Would you rather explore a new kink or revisit a favorite?",
        "Would you rather be completely spontaneous or have every detail planned?",
        "Would you rather have chemistry immediately or develop it slowly?",
    ],
}


# ==========================================================
# NEVER HAVE I EVER
# ==========================================================

NEVER_HAVE_I_EVER = {

    "mild": [

        "Never have I ever flirted with someone I just met.",
        "Never have I ever had a crush on someone in this group.",
        "Never have I ever stayed up all night talking to someone.",
        "Never have I ever gone on a completely spontaneous date.",
        "Never have I ever sent a risky text and immediately regretted it.",
        "Never have I ever fallen for someone's personality before their looks.",
        "Never have I ever pretended not to notice someone flirting with me.",
        "Never have I ever had chemistry with someone completely unexpected.",
        "Never have I ever had a secret crush.",
        "Never have I ever made the first move.",
        "Never have I ever gotten nervous around someone attractive.",
        "Never have I ever gone on a date without knowing where we were going.",
        "Never have I ever flirted through emojis.",
        "Never have I ever had a crush on a friend's friend.",
        "Never have I ever planned an entire date in my head before asking someone out.",
    ],

    "spicy": [

        "Never have I ever sent a flirty photo.",
        "Never have I ever had chemistry with someone I shouldn't have.",
        "Never have I ever flirted with someone just to see what would happen.",
        "Never have I ever had an adults-only adventure while traveling.",
        "Never have I ever used flirting to get myself out of trouble.",
        "Never have I ever had a fantasy about someone I barely knew.",
        "Never have I ever kissed someone on the first date.",
        "Never have I ever deliberately teased someone because I knew they liked it.",
        "Never have I ever had a secret attraction to someone.",
        "Never have I ever stayed up all night because the chemistry was too good.",
        "Never have I ever had a date turn into something completely unexpected.",
        "Never have I ever flirted with more than one person at the same time.",
        "Never have I ever had an adventurous date.",
        "Never have I ever discussed a fantasy with a partner.",
        "Never have I ever surprised a partner with something adventurous.",
    ],

    "extreme": [

        "Never have I ever explored a kink with a consenting partner.",
        "Never have I ever had a fantasy I was nervous to admit.",
        "Never have I ever considered an adventure completely outside my comfort zone.",
        "Never have I ever had chemistry with someone I never expected.",
        "Never have I ever discussed a fantasy with more than one consenting adult.",
        "Never have I ever intentionally pushed my own boundaries in a consensual experience.",
        "Never have I ever tried something adventurous just because someone dared me.",
        "Never have I ever had an adults-only experience while traveling.",
        "Never have I ever had a fantasy become reality.",
        "Never have I ever kept a fantasy secret for a long time.",
        "Never have I ever explored something new because I trusted my partner.",
        "Never have I ever had an experience that completely surprised me.",
        "Never have I ever said yes to an adventure I originally thought I would refuse.",
        "Never have I ever had a conversation that immediately changed the chemistry between us.",
        "Never have I ever tried something outside my usual type.",
    ],
}


# ==========================================================
# MOST LIKELY TO
# ==========================================================

MOST_LIKELY = {

    "mild": [

        "Who is most likely to make the first move?",
        "Who is most likely to plan the perfect date?",
        "Who is most likely to flirt first?",
        "Who is most likely to fall for someone's personality?",
        "Who is most likely to suggest a spontaneous adventure?",
        "Who is most likely to stay up all night talking?",
        "Who is most likely to give the best compliment?",
        "Who is most likely to have a secret crush?",
        "Who is most likely to make everyone laugh?",
        "Who is most likely to organize a group date?",
        "Who is most likely to send the first message?",
        "Who is most likely to get shy around someone attractive?",
        "Who is most likely to travel on a whim?",
        "Who is most likely to make a romantic gesture?",
        "Who is most likely to start a playful argument?",
    ],

    "spicy": [

        "Who is most likely to send the first flirty message?",
        "Who is most likely to make someone blush?",
        "Who is most likely to suggest an adventurous date?",
        "Who is most likely to tease someone on purpose?",
        "Who is most likely to have the boldest fantasy?",
        "Who is most likely to make the first move?",
        "Who is most likely to turn flirting into chemistry?",
        "Who is most likely to plan an adults-only adventure?",
        "Who is most likely to surprise their partner?",
        "Who is most likely to have a secret crush?",
        "Who is most likely to make the group laugh with a spicy answer?",
        "Who is most likely to try something new?",
        "Who is most likely to flirt without realizing it?",
        "Who is most likely to get caught staring?",
        "Who is most likely to turn a casual conversation into flirting?",
    ],

    "extreme": [

        "Who is most likely to suggest the wildest adventure?",
        "Who is most likely to have the boldest fantasy?",
        "Who is most likely to try something completely new?",
        "Who is most likely to plan an unforgettable adults-only night?",
        "Who is most likely to make the first move?",
        "Who is most likely to surprise everyone with their answer?",
        "Who is most likely to have the most adventurous bucket list?",
        "Who is most likely to turn chemistry into an adventure?",
        "Who is most likely to challenge someone to a spicy game?",
        "Who is most likely to say YES to a spontaneous adventure?",
        "Who is most likely to have the most unexpected kink?",
        "Who is most likely to break out of their comfort zone?",
        "Who is most likely to flirt with someone they just met?",
        "Who is most likely to plan something nobody sees coming?",
        "Who is most likely to make someone completely speechless?",
    ],
}


# ==========================================================
# THIS OR THAT
# ==========================================================

THIS_OR_THAT = {

    "mild": [

        "Beach 🏖️ or mountains 🏔️?",
        "Texting 💬 or calling 📞?",
        "Date night 🍷 or game night 🎮?",
        "Romance ❤️ or adventure 🌴?",
        "Morning ☀️ or night 🌙?",
        "Stay home 🏠 or go out 🌃?",
        "Sweet 🍰 or salty 🍿?",
        "Flirting 😏 or teasing 😉?",
        "Movie 🎬 or music 🎶?",
        "Planned date 📅 or spontaneous date 🎲?",
        "Dinner 🍽️ or drinks 🥂?",
        "Dancing 💃 or cuddling 🫂?",
        "Long conversation 💬 or playful banter 😏?",
        "Road trip 🚗 or flight ✈️?",
        "Give compliments 💜 or receive compliments 😌?",
    ],

    "spicy": [

        "Tease 😏 or be teased 😉?",
        "Make the first move 🔥 or be pursued 😈?",
        "Slow burn 🕯️ or instant chemistry ⚡?",
        "Flirty texts 💬 or whispered compliments 🗣️?",
        "Romantic night ❤️ or mischievous night 😈?",
        "Plan everything 📋 or improvise 🎲?",
        "Lead 👑 or follow 😏?",
        "Private chemistry 🤫 or playful public flirting 😉?",
        "Adventure 🌴 or staycation 🏠?",
        "Compliment 💜 or challenge 🔥?",
        "Mystery 🖤 or openness ❤️?",
        "Sweet flirting 😊 or bold flirting 😈?",
        "Couples night 👫 or group adventure 👥?",
        "Conversation 💬 or chemistry 🔥?",
        "Surprise 🎁 or anticipation ⏳?",
    ],

    "extreme": [

        "Fantasy 🔥 or reality 😈?",
        "Lead 👑 or surrender 😏?",
        "Slow burn 🕯️ or intense chemistry 🔥?",
        "Plan everything 📋 or completely spontaneous 🎲?",
        "Try something new 🆕 or perfect a favorite ❤️?",
        "Private 🤫 or adventurous 🌴?",
        "Reveal a fantasy 🔥 or keep it mysterious 🖤?",
        "Challenge someone 😈 or accept a challenge 🔥?",
        "Wild adventure 🌴 or intimate night 🕯️?",
        "Explore 👀 or be surprised 🎁?",
        "Big YES 🔥 or tempting MAYBE 😏?",
        "Confidence 👑 or mystery 🖤?",
        "Chemistry ⚡ or anticipation ⏳?",
        "Bold 😈 or subtle 😉?",
        "Adventure 🎲 or control 👑?",
    ],
}


# ==========================================================
# HOT SEAT
# ==========================================================

HOT_SEAT = {

    "mild": [

        "What is your biggest green flag?",
        "What is your favorite way to flirt?",
        "What instantly attracts you to someone?",
        "What is your perfect date?",
        "What makes you feel comfortable around someone new?",
        "What is your favorite personality trait?",
        "What is something adventurous you want to try?",
        "What is your favorite way to receive attention?",
        "What is something people misunderstand about you?",
        "What is your biggest dating pet peeve?",
    ],

    "spicy": [

        "What is your biggest turn-on?",
        "What is your favorite kind of teasing?",
        "What makes someone irresistible to you?",
        "What is something adventurous on your bucket list?",
        "What kind of flirting gets your attention fastest?",
        "What is your favorite way to build anticipation?",
        "What is one fantasy you would consider exploring?",
        "What kind of chemistry do you find irresistible?",
        "What makes someone unforgettable?",
        "What is your boldest dating experience?",
    ],

    "extreme": [

        "What is your biggest fantasy?",
        "What is one kink you are curious about?",
        "What is your biggest YES?",
        "What is your biggest MAYBE?",
        "What is your absolute HARD NO?",
        "What is the wildest adventure you would consider?",
        "What fantasy have you never admitted out loud?",
        "What would convince you to leave your comfort zone?",
        "What is something you would explore only with someone you trust?",
        "What is the boldest thing you would consider doing on an adults-only date?",
    ],
}


# ==========================================================
# CONFESSIONS
# ==========================================================

CONFESSIONS = {

    "mild": [

        "Confess your biggest dating green flag.",
        "Confess your favorite way to flirt.",
        "Confess something people always misunderstand about you.",
        "Confess your secret favorite type of date.",
        "Confess something that instantly makes you smile.",
        "Confess whether you prefer making the first move.",
        "Confess your biggest dating pet peeve.",
        "Confess one thing you find unexpectedly attractive.",
        "Confess your favorite way to receive attention.",
        "Confess one adventure on your bucket list.",
    ],

    "spicy": [

        "Confess your biggest turn-on.",
        "Confess your favorite kind of teasing.",
        "Confess something you find extremely attractive.",
        "Confess a fantasy you would consider exploring.",
        "Confess your boldest dating experience.",
        "Confess something that instantly creates chemistry for you.",
        "Confess your favorite way to build anticipation.",
        "Confess something adventurous you want to try.",
        "Confess whether you prefer pursuing or being pursued.",
        "Confess something that makes you blush.",
    ],

    "extreme": [

        "Confess your biggest fantasy.",
        "Confess one kink you are curious about.",
        "Confess your biggest YES.",
        "Confess your biggest MAYBE.",
        "Confess your absolute HARD NO.",
        "Confess the wildest adventure you would consider.",
        "Confess something you would only explore with someone you trust.",
        "Confess an experience that changed your perspective on intimacy.",
        "Confess something adventurous that is still on your bucket list.",
        "Confess something you have always wanted to be asked.",
    ],
}


# ==========================================================
# COMPLIMENT BATTLE
# ==========================================================

COMPLIMENT_BATTLE = [

    "Give someone a compliment about their personality.",
    "Give someone a compliment about their energy.",
    "Give someone a compliment that would make them smile.",
    "Give someone a creative compliment.",
    "Give someone a compliment without mentioning appearance.",
    "Tell someone why their vibe stands out.",
    "Give someone your best playful compliment.",
    "Tell someone what makes their personality attractive.",
    "Give someone a compliment they probably don't hear often.",
    "Give someone a bold but respectful compliment.",
    "Tell someone what you appreciate about their energy.",
    "Give someone a compliment in exactly five words.",
    "Give someone a compliment using only emojis.",
    "Give someone your smoothest compliment.",
    "Make someone in the chat feel appreciated.",
]


# ==========================================================
# DICE RESULTS
# ==========================================================

DICE_RESULTS = [

    "🎲 You rolled a 1!",
    "🎲 You rolled a 2!",
    "🎲 You rolled a 3!",
    "🎲 You rolled a 4!",
    "🎲 You rolled a 5!",
    "🎲 You rolled a 6!",
]


# ==========================================================
# COIN RESULTS
# ==========================================================

COIN_RESULTS = [

    "🪙 HEADS!",
    "🪙 TAILS!",
]


# ==========================================================
# END game_data.py
# ==========================================================
