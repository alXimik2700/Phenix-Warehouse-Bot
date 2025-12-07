# bot/keyboards.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def admin_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Загрузить Excel", callback_data="upload_excel")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])