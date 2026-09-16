# ==========================================================
# Melanated AZ Bot launcher
# run_bot.py
#
# Loads the existing bot unchanged, then installs:
#   - Shared QOTD / After Dark topic routing
#   - Question of the Day handlers
#   - Question of the Day scheduler
#   - QOTD submission-panel startup creation
#
# Shared destination:
#   Chat  : -1002697105809
#   Topic : 11999
#
# Render Start Command:
#   python run_bot.py
# ==========================================================

import bot

# This must be imported before question_of_day.py so its fixed routing
# values are in place before question_of_day.py reads its environment.
from topic_routing import install_all_topic_routing

install_all_topic_routing()

from question_of_day import (
    ensure_qotd_submission_panel,
    register_question_of_day_handlers,
    start_question_of_day_scheduler,
)


_original_build_application = bot.build_application


async def _qotd_panel_startup_job(context):
    await ensure_qotd_submission_panel(context.application)


def build_application_with_qotd():
    application = _original_build_application()

    register_question_of_day_handlers(application)
    start_question_of_day_scheduler(application)

    # The QOTD module previously defined the panel creator but did not
    # automatically invoke it during startup. Create/re-pin it after the
    # application is running so the QOTD buttons are always present in
    # topic 11999.
    if application.job_queue:
        application.job_queue.run_once(
            _qotd_panel_startup_job,
            when=2,
            name="qotd-submission-panel-startup",
        )

    return application


bot.build_application = build_application_with_qotd


if __name__ == "__main__":
    bot.main()
