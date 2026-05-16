"""Точка входа: поднимает FastAPI → ngrok-туннель → Telegram-бот."""
from __future__ import annotations

import asyncio
import logging
import time

import uvicorn
from pyngrok import ngrok

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("customers_dream")

PORT = 8888


async def run_webapp():
    config = uvicorn.Config("api.server:app", host="127.0.0.1", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def run_bot():
    from bot.main import main as bot_main
    await bot_main()


async def main():
    # 1. Сначала запускаем веб-сервер
    webapp_task = asyncio.create_task(run_webapp())

    # Даём серверу секунду встать
    await asyncio.sleep(1.5)

    # 2. Поднимаем ngrok-туннель
    logger.info("Starting ngrok tunnel on port %d...", PORT)
    tunnel = ngrok.connect(PORT, "http")
    public_url = tunnel.public_url
    if public_url.startswith("http://"):
        public_url = public_url.replace("http://", "https://")
    logger.info("✅ Mini App URL: %s", public_url)

    # 3. Обновляем WEBAPP_URL в настройках бота
    from bot.config import settings
    settings.webapp_url = public_url

    # 4. Запускаем бота
    bot_task = asyncio.create_task(run_bot())

    logger.info("=" * 50)
    logger.info("Всё запущено!")
    logger.info("Mini App: %s", public_url)
    logger.info("Бот работает. Напиши /start в Telegram.")
    logger.info("=" * 50)

    try:
        await asyncio.gather(webapp_task, bot_task)
    finally:
        ngrok.disconnect(tunnel.public_url)
        ngrok.kill()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        ngrok.kill()
        logger.info("Stopped")
