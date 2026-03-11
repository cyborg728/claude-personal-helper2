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
from bot.models import TranslateWhitelistUser, UserSettings
from bot.services.localization import get_user_locale, t

WAITING_TRANSLATE_USERNAME = 10


async def _get_user_settings(user_id: int) -> UserSettings:
    async with async_session() as session:
        result = await session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        us = result.scalar_one_or_none()
        if not us:
            us = UserSettings(user_id=user_id, translation_enabled=True)
            session.add(us)
            await session.commit()
            await session.refresh(us)
        return us


async def translator_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not await check_access(update, context):
        return
    user = update.effective_user
    if not is_admin(user.username if user else None):
        locale = get_user_locale(user.language_code if user else None)
        await update.message.reply_text(t("admin-only", locale))
        return

    locale = get_user_locale(user.language_code)
    us = await _get_user_settings(user.id)

    toggle_text = (
        t("translator-toggle-off", locale)
        if us.translation_enabled
        else t("translator-toggle-on", locale)
    )

    keyboard = [
        [InlineKeyboardButton(t("translator-add-user", locale), callback_data="tr_add")],
        [
            InlineKeyboardButton(
                t("translator-remove-user", locale), callback_data="tr_remove"
            )
        ],
        [InlineKeyboardButton(toggle_text, callback_data="tr_toggle")],
    ]
    await update.message.reply_text(
        t("translator-title", locale),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def translator_add_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    locale = get_user_locale(user.language_code if user else None)
    await query.edit_message_text(t("translator-add-prompt", locale))
    return WAITING_TRANSLATE_USERNAME


async def translator_add_username(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.effective_user
    locale = get_user_locale(user.language_code if user else None)
    username = update.message.text.strip().lstrip("@").lower()

    async with async_session() as session:
        existing = await session.execute(
            select(TranslateWhitelistUser).where(
                TranslateWhitelistUser.username == username
            )
        )
        if existing.scalar_one_or_none():
            await update.message.reply_text(
                t("translator-user-already-exists", locale, username=username)
            )
            return ConversationHandler.END

        session.add(TranslateWhitelistUser(username=username))
        await session.commit()

    await update.message.reply_text(
        t("translator-user-added", locale, username=username)
    )
    return ConversationHandler.END


async def translator_remove_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    locale = get_user_locale(user.language_code if user else None)

    async with async_session() as session:
        result = await session.execute(select(TranslateWhitelistUser))
        users = result.scalars().all()

    if not users:
        await query.edit_message_text(t("translator-list-empty", locale))
        return

    keyboard = [
        [
            InlineKeyboardButton(
                f"@{u.username}", callback_data=f"tr_del_{u.username}"
            )
        ]
        for u in users
    ]
    await query.edit_message_text(
        t("translator-remove-select", locale),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def translator_delete_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    locale = get_user_locale(user.language_code if user else None)
    username = query.data.replace("tr_del_", "")

    async with async_session() as session:
        result = await session.execute(
            select(TranslateWhitelistUser).where(
                TranslateWhitelistUser.username == username
            )
        )
        db_user = result.scalar_one_or_none()
        if db_user:
            await session.delete(db_user)
            await session.commit()

    await query.edit_message_text(
        t("translator-user-removed", locale, username=username)
    )


async def translator_toggle_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    locale = get_user_locale(user.language_code if user else None)

    async with async_session() as session:
        result = await session.execute(
            select(UserSettings).where(UserSettings.user_id == user.id)
        )
        us = result.scalar_one_or_none()
        if not us:
            us = UserSettings(user_id=user.id, translation_enabled=True)
            session.add(us)
        us.translation_enabled = not us.translation_enabled
        await session.commit()
        enabled = us.translation_enabled

    if enabled:
        await query.edit_message_text(t("translator-enabled", locale))
    else:
        await query.edit_message_text(t("translator-disabled", locale))


def get_handlers() -> list:
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(translator_add_callback, pattern="^tr_add$")
        ],
        states={
            WAITING_TRANSLATE_USERNAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, translator_add_username
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    return [
        CommandHandler("translator", translator_command),
        conv_handler,
        CallbackQueryHandler(translator_remove_callback, pattern="^tr_remove$"),
        CallbackQueryHandler(translator_delete_user, pattern="^tr_del_"),
        CallbackQueryHandler(translator_toggle_callback, pattern="^tr_toggle$"),
    ]
