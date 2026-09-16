# Melanated AZ Bot launcher
# Runtime fixes and Truth/Dare integrations are installed before bot.main().

import bot
import runtime_fixes  # noqa: F401
import qotd_td_user  # noqa: F401
import admin_truth_dare_qotd  # noqa: F401

if __name__ == "__main__":
    bot.main()
