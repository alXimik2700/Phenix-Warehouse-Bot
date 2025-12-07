# main.py

import logging
import sys
import asyncio
import os
from bot.core import PhoenixBot

# Убедимся, что папка для логов существует (на случай будущего расширения)
os.makedirs("logs", exist_ok=True)

# === НАСТРОЙКА ЛОГИРОВАНИЯ (единожды при старте) ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
# Подавляем шум от aiogram
logging.getLogger("aiogram").setLevel(logging.WARNING)
# ===============================================================

# Логгер для основного модуля
logger = logging.getLogger(__name__)


async def main():
    """Основная асинхронная точка входа."""
    logger.info("=" * 50)
    logger.info("🚀 Запуск бота 'Феникс Склад'...")
    logger.info("=" * 50)

    # Проверяем наличие Excel-файла
    if not os.path.exists("Адреса.xlsx"):
        logger.warning("⚠️ Файл 'Адреса.xlsx' не найден. Обновите базу через /admin.")

    bot_instance = PhoenixBot()
    try:
        await bot_instance.start()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки (Ctrl+C)")
    except Exception:
        logger.exception("💥 Непредвиденная ошибка в основном цикле:")
        raise
    finally:
        logger.info("👋 Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Процесс прерван пользователем")
    except Exception:
        logger.exception("💥 Критическая ошибка при запуске:")