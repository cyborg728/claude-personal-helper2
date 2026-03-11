from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.database import async_session
from bot.middleware.access import check_access, is_admin
from bot.models import AllowedUser
from bot.services.localization import get_user_locale, t

WAITING_USERNAME = 1


async def whitelist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_access(update, context):
        return
    user = update.effective_user
    if not is_admin(user.username if user else None):
        locale = get_user_locale(user.language_code if user else None)
        await update.message.reply_text(t("admin-only", locale))
        return

    locale = get_user_locale(user.language_code)
    keyboard = [
        [InlineKeyboardButton("+", callback_data="wl_add")],
        [InlineKeyboardButton("-", callback_data="wl_remove")],
    ]
    await update.message.reply_text(
        t("whitelist-title", locale),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def whitelist_add_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    locale = get_user_locale(user.language_code if user else None)
    await query.edit_message_text(t("whitelist-add-prompt", locale))
    return WAITING_USERNAME


async def whitelist_add_username(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.effective_user
    locale = get_user_locale(user.language_code if user else None)
    username = update.message.text.strip().lstrip("@").lower()

    async with async_session() as session:
        existing = await session.execute(
            select(AllowedUser).where(AllowedUser.username == username)
        )
        if existing.scalar_one_or_none():
            await update.message.reply_text(
                t("whitelist-already-exists", locale, username=username)
            )
            return ConversationHandler.END

        session.add(AllowedUser(username=username))
        await session.commit()

    await update.message.reply_text(t("whitelist-added", locale, username=username))
    return ConversationHandler.END


async def whitelist_remove_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    locale = get_user_locale(user.language_code if user else None)

    async with async_session() as session:
        result = await session.execute(select(AllowedUser))
        users = result.scalars().all()

    if not users:
        await query.edit_message_text(t("whitelist-empty", locale))
        return

    keyboard = [
        [InlineKeyboardButton(f"@{u.username}", callback_data=f"wl_del_{u.username}")]
        for u in users
    ]
    await query.edit_message_text(
        t("whitelist-remove-prompt", locale),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def whitelist_delete_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    locale = get_user_locale(user.language_code if user else None)
    username = query.data.replace("wl_del_", "")

    async with async_session() as session:
        result = await session.execute(
            select(AllowedUser).where(AllowedUser.username == username)
        )
        db_user = result.scalar_one_or_none()
        if db_user:
            await session.delete(db_user)
            await session.commit()

    await query.edit_message_text(t("whitelist-removed", locale, username=username))


def get_handlers() -> list:
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(whitelist_add_callback, pattern="^wl_add$")],
        states={
            WAITING_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, whitelist_add_username)
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    return [
        CommandHandler("whitelist", whitelist_command),
        conv_handler,
        CallbackQueryHandler(whitelist_remove_callback, pattern="^wl_remove$"),
        CallbackQueryHandler(whitelist_delete_user, pattern="^wl_del_"),
    ]
