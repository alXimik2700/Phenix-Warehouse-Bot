# parsers/excel_parser.py

import pandas as pd
import logging
import os
import re
from config import EXCEL_FILE
from database.db_manager import DBManager

# Логгер для этого модуля
logger = logging.getLogger(__name__)


def clean_article(article):
    """Извлекает первый числовой артикул из строки (например, '917 / СВ917Т' → '917')"""
    if pd.isna(article):
        return None

    text = str(article).strip()

    # Ищем первое целое число (игнорируем дроби и слова)
    match = re.search(r'\b(\d+)\b', text)
    if match:
        return match.group(1)

    return None


class ExcelParser:
    @staticmethod
    def parse_and_save():
        """
        Парсит Excel-файл и сохраняет данные в SQLite.
        Возвращает количество загруженных строк.
        """
        logger.info(f"🔁 Начинаю парсинг Excel-файла: {EXCEL_FILE}")

        if not os.path.exists(EXCEL_FILE):
            error_msg = f"❌ Файл не найден: {EXCEL_FILE}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            # Загрузка данных
            df = pd.read_excel(EXCEL_FILE, header=0)
            logger.debug(f"Загружено {len(df)} строк из Excel")

            # Удаляем строки без названия
            initial_len = len(df)
            df = df.dropna(subset=["Номенклатура, Серия"])
            logger.debug(f"Удалено {initial_len - len(df)} строк без названия")

            # Преобразуем "Итого" в число
            df["Итого"] = pd.to_numeric(df["Итого"], errors="coerce")

            # Проверка наличия нужных колонок
            required_cols = [
                "Артикул",
                "Номенклатура.Адрес (Общие)",
                "Номенклатура, Серия",
                "Ед. изм.",
                "Итого"
            ]
            missing_cols = set(required_cols) - set(df.columns)
            if missing_cols:
                error_msg = f"❌ В Excel отсутствуют колонки: {missing_cols}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Подготовка строк с корректной обработкой артикулов
            rows = []
            for _, row in df.iterrows():
                article = clean_article(row["Артикул"])
                address = row["Номенклатура.Адрес (Общие)"] or None
                name = row["Номенклатура, Серия"] or None
                unit = row["Ед. изм."] or "упак"
                quantity = row["Итого"]
                rows.append((article, address, name, unit, quantity))

            logger.debug(f"Подготовлено {len(rows)} строк для вставки в БД")

            # Сохранение в БД
            db = DBManager()
            try:
                db.clear_all()
                db.insert_many(rows)
            finally:
                db.close()

            logger.info(f"✅ Успешно загружено {len(rows)} товаров в базу данных.")
            return len(rows)

        except Exception as e:
            logger.exception("❌ Критическая ошибка при парсинге Excel:")
            raise