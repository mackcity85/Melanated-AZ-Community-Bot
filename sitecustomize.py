"""Early startup hooks for deployments that launch bot.py directly.

Python imports sitecustomize automatically during interpreter startup when this
repository is on sys.path.  This makes the critical introduction recovery and
monthly-reminder fixes load before bot.build_application() captures bot.post_init.
The normal run_bot.py launcher also imports these modules, so each patch is
idempotent and is not applied twice.
"""

import logging

logger = logging.getLogger("melanated_az_startup")

try:
    # Import the real bot first.  bot.py defines post_init and build_application;
    # the two fix modules then wrap bot.post_init before the application is built.
    import bot  # noqa: F401
    import intro_persistence  # noqa: F401
    import intro_reminder_fix  # noqa: F401
    logger.info("Startup hooks loaded: intro persistence + intro reminders")
except Exception:
    # Never prevent the bot process from starting because an optional startup
    # hook failed. The module will still be retried by the normal launcher if
    # run_bot.py is used, and the exception is visible in Render logs.
    logger.exception("Startup hook loading failed")
