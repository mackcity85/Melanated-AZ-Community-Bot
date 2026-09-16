# Truth or Dare QOTD integration loader
import question_of_day as qotd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def install():
    original = qotd.qotd_menu_markup
    def menu():
        markup = original()
        rows = list(markup.inline_keyboard)
        rows.insert(2, [InlineKeyboardButton("🔥 Submit Truth or Dare", callback_data="qotd_submit_truthdare")])
        return InlineKeyboardMarkup(rows)
    qotd.qotd_menu_markup = menu

install()
