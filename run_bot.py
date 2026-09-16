# Melanated AZ Bot launcher
# Install topic routing before any QOTD module is imported so its
# America/Phoenix topic/schedule configuration is loaded correctly.

import bot
import topic_routing

topic_routing.install_all_topic_routing()

import runtime_fixes  # noqa: F401
import qotd_td_user  # noqa: F401
import admin_truth_dare_qotd  # noqa: F401
import intro_persistence  # noqa: F401
import intro_reminder_fix  # noqa: F401
import raffle_manual_nav_fix

raffle_manual_nav_fix.install()

if __name__ == "__main__":
    bot.main()
