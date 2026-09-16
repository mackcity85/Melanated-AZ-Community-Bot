# Melanated AZ Bot launcher
# Runtime fixes are installed before bot.main() registers handlers/jobs.

import bot
import runtime_fixes  # noqa: F401

if __name__ == "__main__":
    bot.main()
