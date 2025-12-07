# bot/handlers.py

import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS
from database.db_manager import DBManager
from parsers.excel_parser import ExcelParser
from bot.keyboards import admin_panel_kb

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Бот склада «Феникс»\n\n"
        "Примеры запросов:\n"
        "- Название: Кубаночка огурцы\n"
        "- С весом: Увелка 0.9 или Увелка 900\n"
        "- Адрес: A-01-02-000\n"
        "- Артикул: Мисо 200"
    )
    logger.info(f"start от @{message.from_user.username} (ID: {message.from_user.id})")


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🔍 Как искать:\n"
        "- Артикул: <code>900</code>\n"
        "- Название: <code>гречка</code>\n"
        "- Адрес: <code>A-01-02-000</code>\n\n"
        "💡 Совет: пишите короче — <code>увелка 900</code>, а не «Увелка Б/П Гречка...»",
        parse_mode="HTML"
    )
    logger.info(f"help от @{message.from_user.username} (ID: {message.from_user.id})")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Доступ запрещён.")
        logger.warning(f"Попытка доступа к /admin от ID: {message.from_user.id}")
        return
    await message.answer("Панель администратора", reply_markup=admin_panel_kb())
    logger.info(f"Админ-панель запрошена ID: {message.from_user.id}")


@router.message(Command("reload_aliases"))
async def reload_aliases_cmd(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        from utils.aliases import reload_aliases
        new_aliases = reload_aliases()
        count = len(new_aliases)
        await message.answer(f"✅ Словарь алиасов обновлён!\nВсего артикулов: {count}")
        logger.info(f"🔄 Алиасы перезагружены админом ID: {message.from_user.id} ({count} записей)")
    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении алиасов: {e}")
        logger.exception("Ошибка перезагрузки алиасов:")


@router.callback_query(F.data == "upload_excel")
async def request_excel(callback: CallbackQuery):
    await callback.message.answer("Отправьте файл Адреса.xlsx")
    await callback.answer()
    logger.info(f"Запрос на загрузку Excel от ID: {callback.from_user.id}")


@router.message(F.document)
async def handle_document(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    if not message.document.file_name.endswith('.xlsx'):
        await message.answer("Поддерживается только .xlsx")
        return

    logger.info(f"Получен Excel от @{message.from_user.username} (ID: {message.from_user.id})")
    temp_path = f"temp_{message.document.file_id}.xlsx"

    try:
        await message.bot.download(message.document, destination=temp_path)
        os.replace(temp_path, "Адреса.xlsx")
        total = ExcelParser.parse_and_save()
        await message.answer(f"База обновлена!\nВсего позиций: {total}")
        logger.info(f"База обновлена: {total} позиций")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        logger.exception("Ошибка при обновлении базы:")
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    with DBManager() as db:
        total = len(db.search(""))
    await callback.message.answer(f"Всего товаров: {total}")
    await callback.answer()
    logger.info(f"Статистика: {total} товаров")


@router.callback_query(F.data == "cancel")
async def cancel(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@router.message()
async def search_product(message: Message):
    query = message.text.strip()
    if not query:
        return

    user = message.from_user
    logger.info(f"Запрос от @{user.username} (ID: {user.id}): '{query}'")

    with DBManager() as db:
        # Поиск по точному адресу
        if len(query) >= 10 and query[1] == '-' and query[0] in "ABCDEFGHKLMNORSTX":
            item = db.get_by_address(query)
            if item:
                name = item[3] or "—"
                address = item[2] or "—"
                balance = item[5] if item[5] is not None else "—"
                unit = item[4] or "упак"
                response = f"{name}\nАдрес: {address}\nОстаток: {balance} {unit}"
                try:
                    await message.answer(response)
                    logger.info(" → Найден по адресу")
                except Exception as e:
                    logger.error(f"Ошибка отправки: {e}")
                    await message.answer("Не удалось отправить результат. Повторите запрос.")
                return
            else:
                await message.answer("Товар по адресу не найден.")
                logger.info(" → Адрес не найден")
                return

        # Поиск по названию
        results = db.search(query)
        if not results:
            await message.answer("Ничего не найдено. Уточните запрос.")
            logger.warning(f"🚫 Ничего не найдено: '{query}' от ID: {user.id}")
            return

        # Формируем сухой текстовый ответ (без ограничения)
        response = ""
        for row in results[:]:  # убран лимит
            name = row[3] or "—"
            address = row[2] or "—"
            balance = row[5] if row[5] is not None else "—"
            unit = row[4] or "упак"
            response += f"{name}\nАдрес: {address}\nОстаток: {balance} {unit}\n\n"

        # Если результатов много — добавляем подсказку
        if len(results) > 5:
            response += f"Ещё {len(results) - 5} позиций. Уточните запрос."

        try:
            await message.answer(response)
            logger.info(f" → Отправлено {len(results)} результатов")
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")
            await message.answer("Ошибка сети. Повторите запрос.")