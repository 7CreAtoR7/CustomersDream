"""Продакшен-точка входа: FastAPI (uvicorn) + Telegram-бот в одном процессе.

Без ngrok! На хостинге наружу смотрит nginx (HTTPS), который проксирует
запросы на 127.0.0.1:8888. Адрес Mini App берётся из переменной WEBAPP_URL
в .env (например, https://your-domain.ru).
"""
from __future__ import annotations

import asyncio
import logging

import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("customers_dream")

# Слушаем только localhost — наружу проксирует nginx (он же даёт HTTPS).
HOST = "127.0.0.1"
PORT = 8888


async def run_webapp() -> None:
    config = uvicorn.Config(
        "api.server:app",
        host=HOST,
        port=PORT,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_bot() -> None:
    from bot.main import main as bot_main
    await bot_main()


async def main() -> None:
    from bot.config import settings

    logger.info("=" * 50)
    logger.info("PROD старт")
    logger.info("Mini App URL (из .env WEBAPP_URL): %s", settings.webapp_url)
    if settings.webapp_url.startswith("http://"):
        logger.warning(
            "WEBAPP_URL не HTTPS! Telegram Mini App требует https:// — "
            "настрой домен и SSL (см. инструкцию)."
        )
    logger.info("=" * 50)

    webapp_task = asyncio.create_task(run_webapp())
    await asyncio.sleep(1.5)
    bot_task = asyncio.create_task(run_bot())

    await asyncio.gather(webapp_task, bot_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped")
