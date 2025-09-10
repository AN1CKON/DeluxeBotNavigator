"""Модуль для создания клавиатур системы отзывов"""

from aiogram import types
from src.handlers.user_interface.review_ui.review_constants import RATING_DESCRIPTIONS
from src.utils.texts import *


async def create_rating_keyboard(selected_rating: int) -> types.InlineKeyboardMarkup:
    """Создает интерактивную клавиатуру для выбора оценки"""
    stars = []

    # Создаем ряд звездочек (от 1 до 5)
    star_row = []
    for i in range(1, 6):
        star_text = "⭐" if i <= selected_rating else "☆"
        star_row.append(
            types.InlineKeyboardButton(
                text=star_text,
                callback_data=f"star_{i}"
            )
        )
    stars.append(star_row)

    # Добавляем кнопки управления
    control_row = [types.InlineKeyboardButton(text="❌ Закрыть", callback_data="close_review")]

    if selected_rating > 0:
        control_row.append(
            types.InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_rating")
        )

    stars.append(control_row)
    return types.InlineKeyboardMarkup(inline_keyboard=stars)


def create_review_form_keyboard() -> types.InlineKeyboardMarkup:
    """Создает клавиатуру для формы отзыва"""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=BUTTON_BACK, callback_data="back_to_rating"),
         types.InlineKeyboardButton(text=BUTTON_CLOSE, callback_data="close_review")]
    ])


def create_success_keyboard() -> types.InlineKeyboardMarkup:
    """Создает клавиатуру для сообщения успеха"""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=BUTTON_OK, callback_data="close_success")]
    ])


def get_rating_description(rating: int) -> str:
    """Возвращает текстовое описание оценки"""
    return RATING_DESCRIPTIONS.get(rating, f"⭐{'⭐' * (rating - 1)}")
