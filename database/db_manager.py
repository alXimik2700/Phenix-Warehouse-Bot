# database/db_manager.py

import sqlite3
import logging
import re
from config import DATABASE_PATH

# Логгер для этого модуля
logger = logging.getLogger(__name__)


class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article TEXT,
                address TEXT,
                name TEXT NOT NULL,
                unit TEXT,
                quantity REAL
            )
        """)
        # Индекс по адресу для быстрого поиска
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_address ON items(address);")
        # Индекс по артикулу для точного поиска
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_article ON items(article);")
        self.conn.commit()
        logger.debug("🗃️ Таблица 'items' и индексы созданы/проверены")

    def clear_all(self):
        self.cursor.execute("DELETE FROM items")
        self.conn.commit()
        logger.debug("🧹 База данных очищена")

    def insert_many(self, rows):
        """
        Вставляет список строк в таблицу.
        rows: список кортежей [(article, address, name, unit, quantity), ...]
        """
        if not rows:
            logger.warning("⚠️ Попытка вставить пустой список в БД")
            return

        try:
            logger.debug(f"📥 Вставка {len(rows)} строк в БД...")
            self.cursor.executemany("""
                INSERT INTO items (article, address, name, unit, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, rows)
            self.conn.commit()
            logger.debug("✅ Вставка завершена успешно")
        except sqlite3.Error as e:
            self.conn.rollback()
            error_msg = f"Ошибка при вставке данных в БД: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_by_address(self, address: str):
        self.cursor.execute("SELECT * FROM items WHERE address = ?", (address,))
        result = self.cursor.fetchone()
        logger.debug(f"🔍 Запрос по адресу '{address}': {'найдено' if result else 'не найдено'}")
        return result

    def search(self, query: str):
        """
        Умный поиск:
        - Если запрос — чисто число → ищем по артикулу (ТОЧНОЕ совпадение)
        - Иначе → гибридный поиск по названию
        """
        if not query.strip():
            self.cursor.execute("SELECT * FROM items")
            return self.cursor.fetchall()

        # Проверяем, является ли запрос чисто числом
        if query.isdigit():
            # Ищем ТОЛЬКО по артикулу (ТОЧНОЕ совпадение)
            self.cursor.execute("SELECT * FROM items WHERE article = ?", (query,))
            results = self.cursor.fetchall()
            logger.debug(f"🔍 Поиск по артикулу '{query}' (чисто число): {len(results)} результатов")
            return results
        else:
            # Гибридный поиск по названию
            from utils.aliases import ALIASES
            from utils.search import expand_query_with_aliases, normalize_for_search

            tokens = expand_query_with_aliases(query, ALIASES)
            if not tokens:
                return []

            self.cursor.execute("SELECT * FROM items")
            all_items = self.cursor.fetchall()

            matched = []
            for item in all_items:
                name = item[3]
                if name is None:
                    continue
                norm_name = normalize_for_search(name)
                matched_tokens = sum(1 for token in tokens if token in norm_name)
                if (len(tokens) <= 2 and matched_tokens == len(tokens)) or (len(tokens) > 2 and matched_tokens >= 2):
                    matched.append(item)
                if len(matched) >= 20:  # лимит для безопасности
                    break

            logger.debug(f"🔍 Гибридный поиск по '{query}' (токены: {tokens}): найдено {len(matched)} результатов")
            return matched

    def search_by_name(self, query: str):
        """Совместимость — делегируем вызов"""
        return self.search(query)

    def close(self):
        """Закрывает соединение с базой данных."""
        if self.conn:
            self.conn.close()
            logger.debug("🔌 Соединение с БД закрыто")

    # Поддержка контекстного менеджера (with DBManager() as db: ...)
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()