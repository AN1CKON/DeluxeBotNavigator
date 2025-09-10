"""Обработчик формы отзыва"""

import asyncio
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from src.handlers.common.utils import safe_delete_message
from src.models import ReviewStates
from src.handlers.user_interface.review_ui import (
    MSG_REVIEW_RATING,
    MSG_REVIEW_FORM,
    MSG_REVIEW_SUCCESS,
    MSG_REVIEW_SUCCESS_WITH_TIMER,
    MSG_REVIEW_ERROR,
    MSG_REVIEW_TOO_SHORT,
    MSG_REVIEW_TOO_LONG
)
from src.handlers.user_interface.review_ui.review_constants import REVIEW_STATES
from src.handlers.user_interface.review_ui.review_keyboard import create_rating_keyboard, create_review_form_keyboard, get_rating_description
from .review_email import send_review_email
from .review_utils import (
    review_state_manager,
    show_success_with_timer,
    validate_review_text,
    get_user_info
)
from .review_spam_protection import spam_protection


async def show_review_form(message: types.Message, state: FSMContext):
    """Показывает форму для написания отзыва"""
    if review_state_manager.is_review_recently_completed():
        review_state_manager.clear_review_completed()
        return

    keyboard = await create_rating_keyboard(0)
    review_form_message = await message.answer(MSG_REVIEW_RATING, reply_markup=keyboard, parse_mode="HTML")
    await state.update_data(review_form_message_id=review_form_message.message_id)
    await state.set_state(ReviewStates.waiting_for_rating)


def register_review_handlers(dp):
    """Регистрация обработчиков формы отзыва"""

    @dp.callback_query(F.data.startswith("star_"))
    async def handle_star_selection(callback: types.CallbackQuery, state: FSMContext):
        """Обработка выбора звезды"""
        star_number = int(callback.data.split("_")[1])
        data = await state.get_data()
        current_rating = data.get('rating', 0)

        if star_number == current_rating:
            await callback.answer("Эта оценка уже выбрана")
            return

        await state.update_data(rating=star_number)
        keyboard = await create_rating_keyboard(star_number)

        descriptions = ["", "Тильт", "Кринж", "Нормис", "Свага", "Полный фарш!"]
        description_text = f"\n\n<b>Выбранная оценка:</b> {star_number}⭐ - {descriptions[star_number]}"
        new_text = MSG_REVIEW_RATING + description_text

        try:
            await callback.message.edit_text(new_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            if "message is not modified" in str(e):
                await callback.answer("Оценка уже выбрана")
                return
            raise e

        await callback.answer()

    @dp.callback_query(F.data == "confirm_rating")
    async def handle_rating_confirmation(callback: types.CallbackQuery, state: FSMContext):
        """Обработка подтверждения оценки"""
        keyboard = create_review_form_keyboard()
        await callback.message.edit_text(MSG_REVIEW_FORM, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(ReviewStates.waiting_for_review_content)
        await callback.answer()

    @dp.callback_query(F.data == "back_to_rating")
    async def handle_back_to_rating(callback: types.CallbackQuery, state: FSMContext):
        """Обработка возврата к выбору оценки"""
        data = await state.get_data()
        current_rating = data.get('rating', 0)
        keyboard = await create_rating_keyboard(current_rating)

        if current_rating > 0:
            descriptions = ["", "Тильт", "Кринж", "Нормис", "Свага", "Полный фарш!"]
            description_text = f"\n\n<b>Выбранная оценка:</b> {current_rating}⭐ - {descriptions[current_rating]}"
            new_text = MSG_REVIEW_RATING + description_text
        else:
            new_text = MSG_REVIEW_RATING

        await callback.message.edit_text(new_text, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(ReviewStates.waiting_for_rating)
        await callback.answer()

    @dp.message(ReviewStates.waiting_for_review_content)
    async def handle_review_content(message: types.Message, state: FSMContext):
        """Обработка текста отзыва"""
        review_text = message.text.strip()
        data = await state.get_data()
        rating = data.get('rating', 5)
        validation_attempts = data.get('validation_attempts', 0)

        # Проверка на спам
        can_review, spam_message = spam_protection.can_leave_review(message.from_user.id)
        if not can_review:
            spam_notification = await message.answer(spam_message, parse_mode="HTML")
            await asyncio.sleep(3)
            await safe_delete_message(spam_notification)
            await safe_delete_message(message)
            return

        # Валидация текста отзыва
        is_valid, error_message = validate_review_text(review_text)
        if not is_valid:
            if validation_attempts == 0:
                warning_msg = await message.answer(error_message, parse_mode="HTML")
                await state.update_data(
                    validation_attempts=1,
                    warning_message_id=warning_msg.message_id,
                    user_message_id=message.message_id
                )
            else:
                await safe_delete_message(message)
            return

        # Удаляем предыдущие сообщения
        await _cleanup_messages(message, state)

        # Записываем факт отправки отзыва для защиты от спама
        spam_protection.record_review(message.from_user.id)

        # Получаем информацию о пользователе и отправляем email
        user_info = get_user_info(message)
        success = send_review_email(review_text, rating, user_info)

        if success:
            review_state_manager.set_review_completed()
            await show_success_with_timer(message)
        else:
            await message.answer(MSG_REVIEW_ERROR, parse_mode="HTML")

        await state.clear()

    @dp.callback_query(F.data == "close_review")
    async def close_review(callback: types.CallbackQuery, state: FSMContext):
        """Закрытие формы отзыва"""
        await safe_delete_message(callback.message)
        await state.clear()
        await callback.answer()

    @dp.callback_query(F.data == "close_success")
    async def close_success(callback: types.CallbackQuery):
        """Закрытие сообщения успеха"""
        review_state_manager.clear_success_message_id()
        review_state_manager.clear_review_completed()
        await safe_delete_message(callback.message)
        await callback.answer()


async def _cleanup_messages(message: types.Message, state: FSMContext):
    """Очистка сообщений после успешной отправки отзыва"""
    data = await state.get_data()

    # Удаляем предупреждение
    warning_message_id = data.get('warning_message_id')
    if warning_message_id:
        try:
            await message.bot.delete_message(message.chat.id, warning_message_id)
        except Exception:
            pass

    # Удаляем предыдущее сообщение пользователя
    user_message_id = data.get('user_message_id')
    if user_message_id:
        try:
            await message.bot.delete_message(message.chat.id, user_message_id)
        except Exception:
            pass

    # Удаляем форму отзыва
    review_form_message_id = data.get('review_form_message_id')
    if review_form_message_id:
        try:
            await message.bot.delete_message(message.chat.id, review_form_message_id)
        except Exception:
            pass

    # Удаляем текущее сообщение пользователя
    await safe_delete_message(message)
