import logging

from sqlalchemy import select
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.database import async_session
from bot.models import TranslateWhitelistUser, UserSettings
from bot.services.gemini import translate_disclaimer, translate_text, transcribe_and_translate
from bot.services.localization import get_user_locale, t
from bot.settings import settings

logger = logging.getLogger(__name__)

_disclaimer_cache: dict[str, str] = {}

KNOWN_DISCLAIMER_LOCALES = {"en", "ru", "ko"}


async def _get_disclaimer(language_code: str | None) -> str:
    locale = get_user_locale(language_code)
    if locale in KNOWN_DISCLAIMER_LOCALES:
        return t("translation-disclaimer", locale)
    lang = language_code or "en"
    if lang in _disclaimer_cache:
        return _disclaimer_cache[lang]
    disclaimer = await translate_disclaimer(lang)
    _disclaimer_cache[lang] = disclaimer
    return disclaimer


async def _is_translation_enabled() -> bool:
    async with async_session() as session:
        result = await session.execute(select(UserSettings).limit(1))
        us = result.scalar_one_or_none()
        if us is None:
            return True
        return us.translation_enabled


async def _is_in_translate_whitelist(username: str | None) -> bool:
    if not username:
        return False
    async with async_session() as session:
        result = await session.execute(
            select(TranslateWhitelistUser).where(
                TranslateWhitelistUser.username == username.lower()
            )
        )
        return result.scalar_one_or_none() is not None


def _detect_target_language(language_code: str | None) -> str:
    if language_code:
        return language_code
    return "en"


async def handle_business_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.business_message
    if not message:
        return

    if not await _is_translation_enabled():
        return

    sender = message.from_user
    if not sender:
        return

    is_from_admin = (
        sender.username
        and sender.username.lower() == settings.admin_username.lower()
    )

    if is_from_admin:
        # Admin is replying to someone via business chat
        if not message.reply_to_message:
            return
        original = message.reply_to_message
        original_sender = original.from_user
        if not original_sender:
            return

        if not await _is_in_translate_whitelist(
            original_sender.username
        ):
            return

        target_lang = _detect_target_language(original_sender.language_code)

        if message.text:
            translated = await translate_text(message.text, target_lang)
            disclaimer = await _get_disclaimer(original_sender.language_code)
            full_message = f"{translated}\n\n_{disclaimer}_"
            await context.bot.send_message(
                chat_id=message.chat.id,
                text=full_message,
                parse_mode="Markdown",
                business_connection_id=message.business_connection_id,
            )

        # Mark the replied message as read
        try:
            await context.bot.read_business_message(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_id=original.message_id,
            )
        except Exception:
            logger.debug("Could not mark message as read", exc_info=True)
    else:
        # Message from a user (not admin) — translate for admin
        if not await _is_in_translate_whitelist(sender.username):
            return

        admin_lang = "ru"  # Admin's language for receiving translations

        if message.text:
            translated = await translate_text(message.text, admin_lang)
            await context.bot.send_message(
                chat_id=message.chat.id,
                text=f"🌐 *{sender.first_name}:*\n{translated}",
                parse_mode="Markdown",
                business_connection_id=message.business_connection_id,
            )
        elif message.voice:
            file = await context.bot.get_file(message.voice.file_id)
            audio_bytes = await file.download_as_bytearray()
            result = await transcribe_and_translate(bytes(audio_bytes), admin_lang)
            await context.bot.send_message(
                chat_id=message.chat.id,
                text=f"🎤 *{sender.first_name}:*\n{result}",
                parse_mode="Markdown",
                business_connection_id=message.business_connection_id,
            )

        # Mark message as read
        try:
            await context.bot.read_business_message(
                business_connection_id=message.business_connection_id,
                chat_id=message.chat.id,
                message_id=message.message_id,
            )
        except Exception:
            logger.debug("Could not mark message as read", exc_info=True)


def get_handlers() -> list:
    return [
        MessageHandler(
            filters.UpdateType.BUSINESS_MESSAGE,
            handle_business_message,
        ),
    ]
