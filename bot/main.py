from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from bot.config import settings
from bot.database.db import async_session_factory, init_db
from bot.handlers import admin, common, user
from bot.middlewares.db import DbSessionMiddleware
from bot.services.seed import seed_initial_data


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("customers_dream")


async def setup_commands(bot: Bot) -> None:
    user_commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="likes", description="Мои избранные макеты"),
    ]
    await bot.set_my_commands(
        user_commands, scope=BotCommandScopeAllPrivateChats()
    )


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    db_mw = DbSessionMiddleware(async_session_factory)
    dp.message.middleware(db_mw)
    dp.callback_query.middleware(db_mw)

    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    await init_db()
    async with async_session_factory() as session:
        await seed_initial_data(session)

    await setup_commands(bot)
    logger.info("Bot is starting. Admins: %s", settings.admin_ids)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
