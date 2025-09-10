"""Вспомогательные функции для системы отзывов"""

import asyncio
from aiogram import types
from src.handlers.user_interface.review_ui.review_constants import SUCCESS_MESSAGE_DURATION, REVIEW_MIN_LENGTH, REVIEW_MAX_LENGTH
from src.handlers.user_interface.review_ui.review_keyboard import create_success_keyboard
from src.handlers.user_interface.review_ui import (
    MSG_REVIEW_SUCCESS_WITH_TIMER,
    MSG_REVIEW_TOO_SHORT,
    MSG_REVIEW_TOO_LONG
)


class ReviewStateManager:
    """Менеджер состояния системы отзывов"""

    def __init__(self):
        self.current_success_message_id = None
        self.review_recently_completed = False

    def set_success_message_id(self, message_id: int):
        """Устанавливает ID сообщения успеха"""
        self.current_success_message_id = message_id

    def clear_success_message_id(self):
        """Очищает ID сообщения успеха"""
        self.current_success_message_id = None

    def set_review_completed(self):
        """Устанавливает флаг завершения отзыва"""
        self.review_recently_completed = True

    def clear_review_completed(self):
        """Очищает флаг завершения отзыва"""
        self.review_recently_completed = False

    def is_review_recently_completed(self) -> bool:
        """Проверяет, был ли отзыв недавно завершен"""
        return self.review_recently_completed

    def get_success_message_id(self) -> int:
        """Возвращает ID сообщения успеха"""
        return self.current_success_message_id


# Глобальный экземпляр менеджера состояния
review_state_manager = ReviewStateManager()


async def show_success_with_timer(message: types.Message, duration: int = SUCCESS_MESSAGE_DURATION):
    """Показывает сообщение успеха с таймером обратного отсчета"""
    keyboard = create_success_keyboard()
    success_message = await message.answer(
        MSG_REVIEW_SUCCESS_WITH_TIMER.format(seconds=duration),
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    review_state_manager.set_success_message_id(success_message.message_id)
    previous_text = MSG_REVIEW_SUCCESS_WITH_TIMER.format(seconds=duration)

    # Запускаем таймер обратного отсчета
    for remaining in range(duration, 0, -1):
        await asyncio.sleep(1)

        # Проверяем, не было ли сообщение удалено пользователем
        if review_state_manager.get_success_message_id() is None:
            break

        new_text = MSG_REVIEW_SUCCESS_WITH_TIMER.format(seconds=remaining)

        if new_text != previous_text:
            try:
                await success_message.edit_text(
                    new_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                previous_text = new_text
            except Exception as e:
                if "message is not modified" not in str(e):
                    break

    # После завершения таймера удаляем сообщение
    if review_state_manager.get_success_message_id() is not None:
        try:
            await success_message.delete()
        except Exception:
            pass

    review_state_manager.clear_review_completed()


def validate_review_text(review_text: str) -> tuple[bool, str]:
    """Валидирует текст отзыва"""
    length = len(review_text.strip())

    if length < REVIEW_MIN_LENGTH:
        return False, MSG_REVIEW_TOO_SHORT.format(length=length)

    if length > REVIEW_MAX_LENGTH:
        return False, MSG_REVIEW_TOO_LONG.format(length=length)

    return True, ""


def get_user_info(message: types.Message) -> dict:
    """Извлекает информацию о пользователе"""
    return {
        'id': message.from_user.id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name
    }
