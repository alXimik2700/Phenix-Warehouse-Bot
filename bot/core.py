# bot/core.py

import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from bot.handlers import router

# Логгер для этого модуля
logger = logging.getLogger(__name__)


class PhoenixBot:
    def __init__(self):
        logger.info("🔧 Инициализация PhoenixBot...")
        self.bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        self.dp.include_router(router)
        logger.info("✅ PhoenixBot инициализирован")

    async def start(self):
        """Запуск polling с подтверждением готовности."""
        try:
            # Проверяем подключение к Telegram и получаем данные бота
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Бот @{bot_info.username} (ID: {bot_info.id}) успешно подключён к Telegram!")
            logger.info("🚀 Бот готов принимать сообщения!")

            # Запускаем polling
            await self.dp.start_polling(self.bot)
        except Exception:
            logger.exception("💥 Ошибка во время polling:")
            raise
        finally:
            logger.info("🔌 Остановка polling завершена")