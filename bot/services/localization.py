import os
from pathlib import Path

from fluent.runtime import FluentLocalization, FluentResourceLoader

from bot.settings import settings

_LOCALES_DIR = Path(__file__).parent.parent / "locales"
_loader = FluentResourceLoader(str(_LOCALES_DIR / "{locale}"))
_cache: dict[str, FluentLocalization] = {}


def _get_localization(locale: str) -> FluentLocalization:
    if locale not in _cache:
        _cache[locale] = FluentLocalization(
            locales=[locale, settings.default_locale],
            resource_ids=["main.ftl"],
            resource_loader=_loader,
        )
    return _cache[locale]


def get_user_locale(language_code: str | None) -> str:
    if language_code and language_code in settings.available_locales:
        return language_code
    return settings.default_locale


def t(key: str, locale: str | None = None, **kwargs) -> str:
    loc = locale or settings.default_locale
    localization = _get_localization(loc)
    return localization.format_value(key, kwargs) or key
