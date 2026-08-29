# ==========================================================
# /games COMMAND
# ==========================================================

async def games_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Open the Melanated AZ Game Center from /games."""

    message = update.effective_message

    if not message:
        return

    await message.reply_text(
        "🎮 <b>MELANATED AZ GAME CENTER</b>\n\n"
        "Choose a category below and pick a game.\n\n"
        "🏆 Play games\n"
        "⭐ Earn XP\n"
        "🪙 Earn AZ Coins\n"
        "📊 Build your game stats!",
        reply_markup=games_home_keyboard(),
        parse_mode=ParseMode.HTML,
    )
