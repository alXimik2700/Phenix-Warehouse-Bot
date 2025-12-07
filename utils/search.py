# utils/search.py

import re


def normalize_for_search(text: str) -> str:
    """
    Приводит текст к каноническому виду для поиска:
    - нижний регистр
    - УДАЛЕНИЕ всех не-буквенно-цифровых символов (не замена на пробел!)
    - расширение весов: 0.9 → 0.9 900
    """
    if not text:
        return ""

    text = str(text).lower()

    # Сохраним исходный текст для обработки весов
    original = text

    # Обработка весов: ищем в исходном тексте шаблоны вроде "0.9", "1.5"
    def expand_weight(match):
        num = match.group(0)
        try:
            if '.' in num:
                grams = str(int(float(num) * 1000))
                return f"{num}{grams}"  # без пробелов!
            else:
                return num
        except:
            return num

    # Находим веса ДО удаления точек
    text_with_weights = re.sub(r'\b\d+\.\d+\b', expand_weight, original)

    # УДАЛЯЕМ все не-буквенно-цифровые символы (остаётся только [а-яa-z0-9])
    clean_text = re.sub(r'[^а-яa-z0-9]', '', text_with_weights)

    return clean_text


def expand_query_with_aliases(query: str, aliases_dict: dict) -> list[str]:
    """
    Расширяет запрос алиасами и возвращает список канонических форм.
    """
    # Нормализуем исходный запрос
    base_form = normalize_for_search(query)
    tokens = set()

    # Добавляем сам запрос как токен
    if base_form:
        tokens.add(base_form)

    # Проверяем алиасы: если в запросе есть цифры, пробуем найти алиас
    digits = ''.join(re.findall(r'\d+', query))
    if digits in aliases_dict:
        # Формируем каноническую форму из ключевых слов алиаса
        alias_keywords = aliases_dict[digits]
        alias_text = ' '.join(alias_keywords)
        alias_form = normalize_for_search(alias_text)
        if alias_form:
            tokens.add(alias_form)

    return list(tokens)


def tokenize_query(query: str) -> list[str]:
    """
    Для обратной совместимости — возвращает каноническую форму как один токен.
    """
    norm = normalize_for_search(query)
    return [norm] if norm else []