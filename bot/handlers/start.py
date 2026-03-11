from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.middleware.access import check_access
from bot.services.localization import get_user_locale, t


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_access(update, context):
        return
    user = update.effective_user
    locale = get_user_locale(user.language_code if user else None)
    await update.message.reply_text(t("welcome", locale))


def get_handlers() -> list:
    return [CommandHandler("start", start_command)]
