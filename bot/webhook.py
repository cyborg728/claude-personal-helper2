import logging

from litestar import Litestar, MediaType, Request, get, post
from telegram import Update

logger = logging.getLogger(__name__)

_application = None


def set_application(app):
    global _application
    _application = app


@post("/webhook", media_type=MediaType.TEXT)
async def webhook_handler(request: Request) -> str:
    if _application is None:
        return "Bot not initialized"
    data = await request.json()
    update = Update.de_json(data=data, bot=_application.bot)
    await _application.process_update(update)
    return "OK"


@get("/health", media_type=MediaType.TEXT)
async def health_check() -> str:
    return "OK"


def create_litestar_app() -> Litestar:
    return Litestar(
        route_handlers=[webhook_handler, health_check],
        debug=False,
    )
