import asyncio
import logging

import uvicorn
from telegram import Update
from telegram.ext import Application

from bot.database import init_db
from bot.handlers import business, start, translator, whitelist
from bot.settings import settings
from bot.webhook import create_litestar_app, set_application

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG if settings.debug else logging.INFO,
)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    app = (
        Application.builder()
        .token(settings.telegram_token)
        .build()
    )

    for module in [start, whitelist, translator, business]:
        for handler in module.get_handlers():
            app.add_handler(handler)

    return app


async def run_polling() -> None:
    await init_db()
    app = build_application()
    logger.info("Starting bot in polling mode...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
    )

    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


async def run_webhook() -> None:
    await init_db()
    app = build_application()
    set_application(app)

    await app.initialize()
    await app.start()
    await app.bot.set_webhook(
        url=settings.webhook_url,
        allowed_updates=Update.ALL_TYPES,
    )
    logger.info("Webhook set to %s", settings.webhook_url)

    litestar_app = create_litestar_app()
    config = uvicorn.Config(
        app=litestar_app,
        host=settings.host,
        port=settings.port,
        log_level="debug" if settings.debug else "info",
    )
    server = uvicorn.Server(config)
    try:
        await server.serve()
    finally:
        await app.stop()
        await app.shutdown()


def main() -> None:
    if settings.mode == "webhook":
        asyncio.run(run_webhook())
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
