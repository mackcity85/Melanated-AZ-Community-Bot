# ==========================================================
# Melanated AZ Bot - Daily Community Messages
# ==========================================================
# Adult, flirty, kinky, and raunchy-but-non-explicit prompts.
# Runs daily through 2027-12-31.
# ==========================================================

import logging
import os
from datetime import date, time
from zoneinfo import ZoneInfo

from telegram.constants import ParseMode
from telegram.error import TelegramError

from games.game_center import GAMES_CHAT_ID

logger = logging.getLogger("melanatedaz.daily_messages")

ARIZONA_TZ = ZoneInfo("America/Phoenix")
DAILY_MESSAGE_HOUR = int(os.environ.get("DAILY_MESSAGE_HOUR", "10") or "10")
DAILY_MESSAGE_MINUTE = int(os.environ.get("DAILY_MESSAGE_MINUTE", "0") or "0")
DAILY_MESSAGE_START = date(2026, 9, 15)
DAILY_MESSAGE_END = date(2027, 12, 31)
DAILY_MESSAGE_JOB_NAME = "melanated-daily-community-message"


DAILY_MESSAGES = [
    ("😈 SPICY CHECK-IN", "What kind of flirting gets your attention before the conversation even starts?"),
    ("🌶️ AFTER-DARK QUESTION", "What is your favorite way to build anticipation without giving everything away?"),
    ("🔥 KINKY CHECK-IN", "What is one kink or fantasy you are curious about exploring with trusted consenting adults?"),
    ("😉 FLIRT ALERT", "Are you the tease, the temptation, or the one who falls for the tease?"),
    ("💋 VIBE CHECK", "What instantly changes someone's energy from 'cute' to 'damn'?"),
    ("😈 CONFESSION TIME", "What is something harmless but naughty that you secretly love?"),
    ("🌶️ CHOOSE YOUR POISON", "Slow-burn chemistry or instant sparks?"),
    ("🔥 ADULTING DIFFERENTLY", "What makes an adults-only night feel unforgettable to you?"),
    ("😉 BOLD QUESTION", "Would you rather make the first move or be pursued?"),
    ("💋 CHEMISTRY TEST", "What matters more: physical attraction, mental chemistry, or the energy between you?"),
    ("😈 TEASE OF THE DAY", "What is your favorite kind of playful teasing?"),
    ("🌶️ SPICY DEBATE", "A confident flirt or a mysterious flirt—which one gets you?"),
    ("🔥 FANTASY FILES", "What is one adventure you would put on your adult bucket list?"),
    ("😉 FIRST IMPRESSION", "What is the first thing you notice when someone catches your eye?"),
    ("💋 MOOD SETTER", "What song instantly puts you in a flirty mood?"),
    ("😈 YES / MAYBE / NO", "What is one thing that is an instant YES, one MAYBE, and one hard NO for you?"),
    ("🌶️ PRIVATE VIBES", "What makes you comfortable enough to take a conversation from public to private?"),
    ("🔥 COUPLE ENERGY", "What makes a couple's chemistry obvious from across the room?"),
    ("😉 FLIRTING STYLE", "Words, eye contact, body language, or a little bit of all three?"),
    ("💋 DATE NIGHT", "What would your ideal adults-only date night look like?"),
    ("😈 DANGEROUSLY ATTRACTIVE", "What personality trait is almost impossible for you to resist?"),
    ("🌶️ SPICY SCENARIO", "Would you rather plan the adventure or let someone surprise you?"),
    ("🔥 CURIOUS MINDS", "What is something adventurous you have always wondered about?"),
    ("😉 GREEN FLAG", "What is the biggest green flag when meeting someone from an adult community?"),
    ("💋 RED FLAG", "What behavior kills the vibe immediately?"),
    ("😈 TEASE OR TEMPT", "Which role fits you better: tease or temptation?"),
    ("🌶️ CHEMISTRY", "What kind of confidence do you find irresistible?"),
    ("🔥 AFTER HOURS", "What makes a night feel like it could turn into a story worth telling?"),
    ("😉 FLIRTY QUESTION", "What compliment would make you blush every single time?"),
    ("💋 VIBE CHECK", "Do you prefer someone direct or someone who makes you wonder?"),
    ("😈 ADULT BUCKET LIST", "Name one experience you would consider with the right consenting people."),
    ("🌶️ BOLD MOVE", "What is the boldest move someone could make that would actually impress you?"),
    ("🔥 SECRET SAUCE", "What makes someone unforgettable after one conversation?"),
    ("😉 FIRST MOVE", "What is your favorite way to let someone know you are interested?"),
    ("💋 FLIRTY CONFESSION", "Have you ever been attracted to someone completely unexpected?"),
    ("😈 KINKY QUESTION", "Do you prefer taking control, giving up control, or switching depending on the vibe?"),
    ("🌶️ SPICY PICK", "Late-night drinks, dancing, private lounge, or spontaneous adventure?"),
    ("🔥 CHEMISTRY TEST", "Can good conversation create attraction before you ever touch?"),
    ("😉 BOUNDARIES", "What is one boundary you always communicate before exploring anything new?"),
    ("💋 AFTER-DARK", "What kind of atmosphere makes you feel your most confident?"),
    ("😈 WHO'S YOUR TYPE?", "What kind of energy makes you look twice?"),
    ("🌶️ PLAYFUL QUESTION", "Would you rather be the one doing the teasing or the one being teased?"),
    ("🔥 ADVENTURE MODE", "What is the wildest date you would actually say yes to?"),
    ("😉 FLIRT SCHOOL", "What is your best non-verbal flirting move?"),
    ("💋 HOT TAKE", "Can someone become more attractive the longer you talk to them?"),
    ("😈 FANTASY FRIDAY", "What fantasy would you explore only after building serious trust?"),
    ("🌶️ VIBE MATCH", "Would you rather meet someone at a party, event, lounge, or online first?"),
    ("🔥 CONFIDENCE", "What makes you feel especially attractive?"),
    ("😉 SPICY POLL", "Mystery or transparency—which creates better tension?"),
    ("💋 DATE NIGHT POLL", "Dress up and go out, or stay in and create your own vibe?"),
    ("😈 ADULT COMMUNITY", "What makes someone feel safe and welcome in a spicy social setting?"),
    ("🌶️ CHEMISTRY", "What is more attractive: confidence, humor, intelligence, or charm?"),
    ("🔥 BOLD QUESTION", "What is something you would try if you knew there would be zero pressure?"),
    ("😉 FLIRT ALERT", "What is your favorite way to receive attention?"),
    ("💋 SPICY CONFESSION", "What innocent-looking thing can be surprisingly seductive?"),
    ("😈 POWER PLAY", "Do you naturally lead, follow, or switch depending on the person?"),
    ("🌶️ KINKY CHECK", "What makes a playful kink conversation feel comfortable instead of awkward?"),
    ("🔥 AFTER HOURS", "What is your ideal time for a spontaneous late-night adventure?"),
    ("😉 LOOKING TWICE", "What style or fashion choice always catches your attention?"),
    ("💋 FLIRTY QUESTION", "What kind of eye contact is too much—or exactly enough?"),
    ("😈 DARE WITHOUT THE DARE", "Describe your ideal spicy night using only three words."),
    ("🌶️ SPICY CHOICE", "One unforgettable night or a slow-burn connection that keeps getting hotter?"),
    ("🔥 CURIOUS", "What is one thing you would love to learn about a potential partner before getting closer?"),
    ("😉 GREEN FLAGS", "What communication habit makes you trust someone faster?"),
    ("💋 MOOD", "What kind of compliment feels better: sexy, beautiful, irresistible, or clever?"),
    ("😈 TEASING", "What is your favorite way to keep someone guessing?"),
    ("🌶️ ADULT NIGHT OUT", "What makes a party or social event feel worth coming back to?"),
    ("🔥 SPARKS", "What makes you realize the chemistry is real?"),
    ("😉 FLIRTING", "Do you flirt more with your eyes, your words, or your attitude?"),
    ("💋 BOLD QUESTION", "What is one compliment you would love to hear from someone you are attracted to?"),
    ("😈 KINKY VIBES", "What matters more when exploring: trust, communication, chemistry, or spontaneity?"),
    ("🌶️ SPICY CHECK", "What is your favorite kind of anticipation?"),
    ("🔥 ADULT BUCKET LIST", "What experience belongs on your someday list?"),
    ("😉 CONFIDENCE", "What makes you feel like the hottest version of yourself?"),
    ("💋 FLIRTY PICK", "Would you rather get a bold compliment or a subtle one that keeps you thinking?"),
    ("😈 AFTER DARK", "What is the most important ingredient in a memorable adults-only night?"),
    ("🌶️ SPICY DEBATE", "Is jealousy ever sexy, or does it kill the vibe?"),
    ("🔥 CHEMISTRY", "How quickly can you tell when someone has your attention?"),
    ("😉 PRIVATE CHAT", "What makes you comfortable taking a flirty conversation into DMs?"),
    ("💋 PLAYFUL", "What is your favorite way to make someone blush?"),
    ("😈 BOUNDARY CHECK", "What is one thing you need someone to ask before taking a situation further?"),
    ("🌶️ ADVENTURE", "Would you rather be surprised with the plan or know exactly what is coming?"),
    ("🔥 SPICY QUESTION", "What is something that can instantly turn a boring conversation into chemistry?"),
    ("😉 FLIRT TEST", "What is your favorite opening line when you really want someone's attention?"),
    ("💋 HOT OR NOT", "Confidence without arrogance—hot or not?"),
    ("😈 FANTASY FILE", "What kind of fantasy requires the most trust for you?"),
    ("🌶️ VIBE CHECK", "What makes someone feel dangerously fun without being disrespectful?"),
    ("🔥 AFTER DARK", "What is your perfect setting for a flirty conversation?"),
    ("😉 SPICY POLL", "Slow dancing or dirty dancing?"),
    ("💋 ATTRACTED", "What is one unexpected quality that can make someone irresistible?"),
    ("😈 PLAYFUL QUESTION", "Would you rather be caught staring or caught smiling at someone?"),
    ("🌶️ TRUST", "What earns your trust fastest when exploring something new?"),
    ("🔥 ADVENTURE MODE", "What would make you say 'why the hell not' to a new experience?"),
    ("😉 FLIRTY CONFESSION", "What is your favorite type of attention from someone you like?"),
    ("💋 SPICY", "What kind of energy makes you want to stay a little longer?"),
    ("😈 CONTROL", "What is more fun: taking charge or letting someone else lead?"),
    ("🌶️ KINKY CHECK", "What is the most important rule for a fun, consensual adult adventure?"),
    ("🔥 DATE NIGHT", "What is one thing that instantly upgrades a date?"),
    ("😉 EYE CONTACT", "How long is too long for eye contact with someone you find attractive?"),
    ("💋 BOLD", "What would make you immediately want to know more about someone?"),
    ("😈 TEASE", "What is your favorite way to create tension without crossing a boundary?"),
    ("🌶️ SPICY CHOICE", "Flirty texting or flirty face-to-face conversation?"),
    ("🔥 CONFIDENCE CHECK", "What is one thing you will never apologize for wanting in an adult connection?"),
    ("😉 CHEMISTRY", "Can a person's voice be a major attraction for you?"),
    ("💋 AFTER HOURS", "What is your favorite kind of late-night conversation?"),
    ("😈 FANTASY", "What is one adventure you would discuss with a partner before ever trying it?"),
    ("🌶️ SPICY QUESTION", "What is the difference between being flirtatious and being too forward?"),
    ("🔥 VIBE", "What kind of person makes you forget to check your phone?"),
    ("😉 FLIRT ALERT", "What is your favorite emoji when the conversation gets spicy?"),
    ("💋 CONFESSION", "What is something that looks innocent but feels extremely flirty?"),
    ("😈 ADULT COMMUNITY", "What is one thing you wish more people understood about consent and communication?"),
    ("🌶️ KINKY", "Do you prefer planned adventures or spontaneous ones?"),
    ("🔥 HOT TAKE", "Does confidence make someone sexier than perfect looks?"),
    ("😉 SPICY POLL", "Would you rather receive a surprise invitation or make the invitation?"),
    ("💋 CHEMISTRY", "What makes you want a second conversation?"),
    ("😈 AFTER DARK", "What is one thing that can turn an ordinary evening into a memorable one?"),
    ("🌶️ TEASER", "What is your favorite way to flirt without saying a word?"),
    ("🔥 ADVENTURE", "What is your ideal balance of comfort and excitement?"),
    ("😉 BOLD QUESTION", "What makes someone confident enough to be attractive but respectful enough to be trusted?"),
    ("💋 FLIRTY", "What compliment would you give someone whose vibe you really liked?"),
    ("😈 KINKY CHECK", "What makes trying something new feel exciting rather than intimidating?"),
    ("🌶️ SPICY", "What kind of teasing makes you laugh and blush at the same time?"),
    ("🔥 DATE VIBES", "What is better: a planned romantic night or a completely spontaneous one?"),
    ("😉 ATTRACTED", "What is a green flag you find surprisingly sexy?"),
    ("💋 AFTER DARK", "What kind of conversation can keep you awake way past bedtime?"),
    ("😈 BOLD", "What is one thing you would ask someone if you knew they could answer honestly?"),
    ("🌶️ PLAYFUL", "What is your favorite way to challenge someone's confidence?"),
    ("🔥 CHEMISTRY", "What makes a connection feel different from ordinary flirting?"),
    ("😉 FLIRTING", "What is your favorite way to show someone you want them to keep talking?"),
    ("💋 SPICY CONFESSION", "What is your biggest weakness when someone knows exactly how to flirt with you?"),
    ("😈 TRUST", "What is one conversation every adventurous adult should have before exploring together?"),
    ("🌶️ CHOICE", "Mystery, confidence, humor, or seduction—which wins you over fastest?"),
    ("🔥 AFTER HOURS", "What is your favorite setting for getting to know someone with chemistry?"),
    ("😉 VIBE CHECK", "What makes someone instantly feel approachable to you?"),
    ("💋 DATE NIGHT", "What is one small detail that can make a date feel luxurious?"),
    ("😈 TEASE", "What is more fun: giving someone butterflies or getting them yourself?"),
    ("🌶️ SPICY QUESTION", "Would you rather have a partner who is bold or one who is unpredictable?"),
    ("🔥 FANTASY FILES", "What is a fantasy you would only share with someone you completely trust?"),
    ("😉 FLIRT ALERT", "What is the smoothest compliment you have ever received?"),
    ("💋 CONFIDENCE", "What makes you feel irresistible without anyone else saying a word?"),
    ("😈 KINKY", "What is one playful rule you would add to a spicy date night?"),
    ("🌶️ ADVENTURE", "Would you rather discover a new place together or turn your own space into an adventure?"),
    ("🔥 CHEMISTRY", "What makes you want to keep learning about someone?"),
    ("😉 SPICY DEBATE", "Can friendship chemistry turn into attraction—or is that a recipe for trouble?"),
    ("💋 AFTER DARK", "What kind of music belongs on a perfect grown-folks night?"),
    ("😈 BOLD QUESTION", "What is one thing you find attractive that other people might overlook?"),
    ("🌶️ TEASING", "What is your favorite way to keep a little mystery alive?"),
    ("🔥 ADULT VIBES", "What makes an adult social event feel comfortable, fun, and flirty?"),
    ("😉 FIRST MOVE", "What is your favorite way to make the first move without being pushy?"),
    ("💋 SPICY", "What is one thing that can make a normal conversation feel electric?"),
    ("😈 TRUST & PLAY", "What is the best way to communicate boundaries without killing the fun?"),
    ("🌶️ CHOOSE", "One-on-one chemistry or group energy—which is more exciting?"),
    ("🔥 AFTER HOURS", "What kind of spontaneous invitation would be impossible for you to ignore?"),
    ("😉 FLIRTY", "What is your favorite way to tell someone 'I'm interested' without saying it directly?"),
    ("💋 CONFESSION", "What is a harmless guilty pleasure that makes you feel a little naughty?"),
    ("😈 KINKY CHECK", "What makes a person trustworthy enough to explore something adventurous with?"),
    ("🌶️ SPICY", "What kind of tension is the most fun: playful, romantic, mysterious, or competitive?"),
    ("🔥 VIBE", "What is one quality that can make someone more attractive every time you see them?"),
    ("😉 BOLD", "Would you rather be told exactly what someone wants or have them make you guess?"),
    ("💋 ADULT DATE", "What is your dream grown-folks night from start to finish?"),
    ("😈 TEASE", "What is the best kind of playful challenge for someone you are flirting with?"),
    ("🌶️ CHEMISTRY", "What makes you think 'yeah, I could get into trouble with this person'?"),
    ("🔥 SPICY QUESTION", "What is something you find sexy about confidence that has nothing to do with looks?"),
    ("😉 FLIRT ALERT", "What is your go-to move when you know the attraction is mutual?"),
    ("💋 AFTER DARK", "What is one thing that makes an evening feel more intimate without getting explicit?"),
    ("😈 FANTASY", "What kind of adventure would you want to plan with a trusted partner?"),
    ("🌶️ ADULT COMMUNITY", "What makes you feel respected and desired at the same time?"),
    ("🔥 BOLD", "What is a question you wish people asked more often before flirting with you?"),
    ("😉 VIBE CHECK", "What is the quickest way for someone to make you smile?"),
    ("💋 SPICY", "What kind of compliment sticks with you long after the conversation ends?"),
    ("😈 CONTROL", "Would you rather set the pace or let someone else set it?"),
    ("🌶️ KINKY", "What makes a playful power dynamic fun and respectful?"),
    ("🔥 CHEMISTRY", "What is the difference between attraction and real chemistry for you?"),
    ("😉 FLIRTING", "What is your favorite way to turn a normal hello into a conversation?"),
    ("💋 DATE NIGHT", "What is your perfect combination of food, music, conversation, and vibes?"),
    ("😈 AFTER DARK", "What is one thing that makes you want to stay out just a little longer?"),
    ("🌶️ SPICY DEBATE", "Is slow-burn chemistry hotter than instant attraction?"),
    ("🔥 ADVENTURE", "What is one new experience you would happily put on the calendar?"),
    ("😉 BOLD QUESTION", "What is your biggest green flag when it comes to flirting?"),
    ("💋 CONFESSION", "What is something someone can do that makes you immediately feel desired?"),
    ("😈 KINKY CHECK", "What is your favorite part of negotiating an adventurous experience?"),
    ("🌶️ TEASE", "What is your favorite way to keep someone intrigued?"),
    ("🔥 VIBE", "What kind of energy makes you want to know someone's whole story?"),
    ("😉 SPICY", "What is your favorite kind of playful banter?"),
    ("💋 AFTER HOURS", "What is the best kind of conversation to have after midnight?"),
    ("😈 FANTASY FILE", "What is one fantasy you would discuss before deciding whether to explore it?"),
    ("🌶️ CHOICE", "Bold invitation or subtle hint—which would you rather receive?"),
    ("🔥 CHEMISTRY", "What makes a person magnetic to you?"),
    ("😉 FLIRT ALERT", "What is your favorite sign that someone is flirting back?"),
    ("💋 ADULT VIBES", "What makes a social space feel sexy without becoming uncomfortable?"),
    ("😈 PLAYFUL", "What is your favorite way to make a date more adventurous?"),
    ("🌶️ SPICY", "What is one thing that instantly makes a person more intriguing?"),
    ("🔥 BOLD", "What is one boundary that actually makes exploring feel more exciting?"),
    ("😉 VIBE CHECK", "What is your favorite kind of chemistry: funny, intellectual, romantic, or physical?"),
    ("💋 FLIRTY", "What is the most memorable way someone has made you feel attractive?"),
    ("😈 KINKY", "What makes a kink conversation fun, respectful, and pressure-free?"),
    ("🌶️ AFTER DARK", "What kind of night makes you forget what time it is?"),
    ("🔥 ADVENTURE", "Would you rather plan a whole spicy weekend or improvise one night?"),
    ("😉 FIRST IMPRESSION", "What makes you immediately comfortable talking to someone new?"),
    ("💋 SPICY QUESTION", "What is something that can be incredibly seductive without being sexual?"),
    ("😈 TEASE", "What is more fun: anticipation or the surprise?"),
    ("🌶️ CHEMISTRY", "What is your favorite kind of tension between two people?"),
    ("🔥 CONFIDENCE", "What is something you wish more people felt confident enough to say out loud?"),
    ("😉 FLIRT ALERT", "What is your favorite way to let someone know they have your attention?"),
    ("💋 ADULT NIGHT", "What is one ingredient every good grown-folks night needs?"),
    ("😈 FANTASY", "What kind of adventure would require the most communication before you said yes?"),
    ("🌶️ BOLD", "What is one thing that can make someone go from interesting to irresistible?"),
    ("🔥 VIBE", "What is your favorite thing about meeting people who are open-minded?"),
    ("😉 SPICY", "Would you rather be surprised with a compliment or a flirty invitation?"),
    ("💋 CONFESSION", "What is your favorite guilty pleasure for a grown-folks night in?"),
    ("😈 TRUST", "What is one thing someone can do that tells you they respect your boundaries?"),
    ("🌶️ TEASING", "What is the most fun kind of harmless temptation?"),
    ("🔥 CHEMISTRY", "What makes a connection feel worth exploring instead of just flirting?"),
    ("😉 AFTER DARK", "What is your favorite way to wind down after a very flirty night?"),
    ("💋 DATE NIGHT", "What is one detail that would make you say 'this person gets me'?"),
    ("😈 KINKY CHECK", "Would you rather try something new together or perfect something you already love?"),
    ("🌶️ SPICY DEBATE", "Is mystery sexy when there is already trust?"),
    ("🔥 ADVENTURE", "What is one destination you would love to visit with someone you have chemistry with?"),
    ("😉 FLIRTING", "What is the difference between confidence and arrogance when flirting?"),
    ("💋 BOLD", "What is one question that instantly tells you whether someone is your vibe?"),
    ("😈 AFTER HOURS", "What is your favorite kind of playful trouble?"),
    ("🌶️ SPICY", "What makes someone a great flirt?"),
    ("🔥 FINAL WORD", "What is one thing you want more of in your adult social life this year?"),
]


def _main_group_id():
    try:
        return int(os.environ.get("MAIN_GROUP_ID", str(GAMES_CHAT_ID)) or str(GAMES_CHAT_ID))
    except (TypeError, ValueError):
        return GAMES_CHAT_ID


async def send_daily_community_message(context):
    today = datetime_today = __import__("datetime").datetime.now(ARIZONA_TZ).date()

    if today < DAILY_MESSAGE_START or today > DAILY_MESSAGE_END:
        logger.info("Daily community message skipped outside configured date range: %s", today)
        return

    chat_id = _main_group_id()
    if not chat_id:
        return

    # Deterministic rotation means restarts do not reset the sequence.
    index = (today - DAILY_MESSAGE_START).days % len(DAILY_MESSAGES)
    title, prompt = DAILY_MESSAGES[index]

    text = (
        f"<b>{title}</b>\n\n"
        f"{prompt}\n\n"
        "😈 Keep it grown, keep it respectful, and remember: PASS is always allowed.\n"
        "👇 Drop your answer and see who matches your energy."
    )

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
        )
        logger.info("Daily community message posted | date=%s | index=%s", today, index)
    except TelegramError:
        logger.exception("Could not send daily community message.")


def start_daily_community_messages(application):
    if not getattr(application, "job_queue", None):
        logger.warning("Daily community messages unavailable: JobQueue not installed.")
        return

    for job in application.job_queue.get_jobs_by_name(DAILY_MESSAGE_JOB_NAME):
        job.schedule_removal()

    application.job_queue.run_daily(
        send_daily_community_message,
        time(
            hour=DAILY_MESSAGE_HOUR,
            minute=DAILY_MESSAGE_MINUTE,
            tzinfo=ARIZONA_TZ,
        ),
        name=DAILY_MESSAGE_JOB_NAME,
    )

    logger.info(
        "Daily community messages scheduled | %02d:%02d Arizona | through %s | %s prompts",
        DAILY_MESSAGE_HOUR,
        DAILY_MESSAGE_MINUTE,
        DAILY_MESSAGE_END.isoformat(),
        len(DAILY_MESSAGES),
    )
