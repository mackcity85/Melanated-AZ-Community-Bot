# ==========================================================
# Melanated AZ Bot launcher
# run_bot.py
#
# Loads the existing bot unchanged, then installs the Question
# of the Day feature before the existing main() starts polling.
#
# Render Start Command:
#   python run_bot.py
# ==========================================================

import bot
from question_of_day import register_question_of_day_handlers, start_question_of_day_scheduler


_original_build_application = bot.build_application


def build_application_with_qotd():
    application = _original_build_application()
    register_question_of_day_handlers(application)
    start_question_of_day_scheduler(application)
    return application


bot.build_application = build_application_with_qotd


if __name__ == "__main__":
    bot.main()
