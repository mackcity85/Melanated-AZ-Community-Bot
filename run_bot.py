# ==========================================================
# Melanated AZ Bot — unified launcher
#
# bot.py is now the single source of truth for:
#   - Telegram handlers
#   - scheduled jobs
#   - topic routing
#   - media routing
#   - admin/event/raffle extensions
#   - Games/Dirty Minds startup hooks
#
# This file intentionally contains no second application builder,
# no second post_init, and no second scheduler definitions.
# ==========================================================

import bot

if __name__ == "__main__":
    bot.main()
