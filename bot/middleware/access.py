from sqlalchemy import select
from telegram import Update
from telegram.ext import ContextTypes

from bot.database import async_session
from bot.models import AllowedUser
from bot.services.localization import get_user_locale, t
from bot.settings import settings


async def is_user_allowed(username: str | None) -> bool:
    if not username:
        return False
    if username.lower() == settings.admin_username.lower():
        return True
    async with async_session() as session:
        result = await session.execute(
            select(AllowedUser).where(AllowedUser.username == username.lower())
        )
        return result.scalar_one_or_none() is not None


def is_admin(username: str | None) -> bool:
    if not username:
        return False
    return username.lower() == settings.admin_username.lower()


async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user or not user.username:
        if update.effective_message:
            locale = get_user_locale(user.language_code if user else None)
            await update.effective_message.reply_text(t("access-denied", locale))
        return False

    if not await is_user_allowed(user.username):
        locale = get_user_locale(user.language_code)
        if update.effective_message:
            await update.effective_message.reply_text(t("access-denied", locale))
        return False

    return True
