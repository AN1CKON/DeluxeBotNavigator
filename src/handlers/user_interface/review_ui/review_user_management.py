"""Управление пользователями и их лимитами в системе отзывов"""

import time
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.handlers.common.utils import is_admin, safe_delete_message
from src.models import AdminStates
from src.utils.texts import (
    NO_ACCESS_MESSAGE, CALLBACK_MANAGE_REVIEWS, CALLBACK_CHECK_USER_REVIEWS,
    MSG_ENTER_USER_ID, MSG_INVALID_USER_ID, MSG_USER_STATS_HEADER,
    MSG_USER_NO_REVIEWS, MSG_USER_LIMITS_RESET_SUCCESS, MSG_LAST_REVIEW_TIME,
    MSG_REVIEWS_TODAY, MSG_TIME_UNTIL_NEXT, MSG_USER_STATUS,
    MSG_USER_STATUS_READY, MSG_USER_STATUS_WAITING, BUTTON_RESET_LIMITS,
    CALLBACK_RESET_USER_LIMITS_PREFIX
)
from src.database.base import get_db
from src.handlers.user_interface.review_logic.review_spam_protection import spam_protection


def register_review_user_management_handlers(dp):
    """Регистрация обработчиков для управления пользователями отзывов"""

    @dp.callback_query(F.data == CALLBACK_CHECK_USER_REVIEWS)
    async def check_user_reviews_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработчик проверки отзывов пользователя"""
        if not is_admin(callback.from_user.id):
            try:
                return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
            except Exception:
                return

        await safe_delete_message(callback.message)
        await callback.message.answer(
            MSG_ENTER_USER_ID,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=CALLBACK_MANAGE_REVIEWS)]]
            )
        )
        await state.set_state(AdminStates.waiting_for_user_id)

    @dp.message(AdminStates.waiting_for_user_id)
    async def handle_user_id_input(message: types.Message, state: FSMContext):
        """Обработка ввода ID пользователя"""
        if not is_admin(message.from_user.id):
            await state.clear()
            return

        try:
            user_id = int(message.text.strip())

            # Получаем статистику пользователя
            user_stats = get_user_review_stats(user_id)

            if user_stats:
                text = f"""<b>{MSG_USER_STATS_HEADER.format(user_id=user_id)}</b>

{MSG_LAST_REVIEW_TIME.format(last_review_time=user_stats['last_review_time'])}
{MSG_REVIEWS_TODAY.format(reviews_today=user_stats['reviews_today'])}
{MSG_TIME_UNTIL_NEXT.format(time_until_next=user_stats['time_until_next'])}

<b>{MSG_USER_STATUS}</b> {user_stats['status']}"""
            else:
                text = MSG_USER_NO_REVIEWS.format(user_id=user_id)

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=BUTTON_RESET_LIMITS, callback_data=f"{CALLBACK_RESET_USER_LIMITS_PREFIX}{user_id}")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data=CALLBACK_MANAGE_REVIEWS)]
                ]
            )

            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

        except ValueError:
            await message.answer(
                MSG_INVALID_USER_ID,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=CALLBACK_MANAGE_REVIEWS)]]
                )
            )
            return

        await state.clear()

    @dp.callback_query(F.data.startswith(CALLBACK_RESET_USER_LIMITS_PREFIX))
    async def reset_user_limits_callback(callback: types.CallbackQuery):
        """Обработчик сброса лимитов конкретного пользователя"""
        if not is_admin(callback.from_user.id):
            try:
                return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
            except Exception:
                return

        user_id = int(callback.data.split(CALLBACK_RESET_USER_LIMITS_PREFIX)[1])

        # Сбрасываем лимиты пользователя
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE user_review_limits
                SET reviews_today = 0, last_reset_date = date('now')
                WHERE user_id = ?
            """, (user_id,))
            conn.commit()

        try:
            await callback.answer(MSG_USER_LIMITS_RESET_SUCCESS.format(user_id=user_id), show_alert=True)
        except Exception:
            pass
        await safe_delete_message(callback.message)


def get_user_review_stats(user_id: int) -> dict:
    """Получает статистику пользователя по отзывам"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT last_review_time, reviews_today, last_reset_date
            FROM user_review_limits
            WHERE user_id = ?
        """, (user_id,))

        result = c.fetchone()
        if result:
            last_review_time, reviews_today, last_reset_date = result
            current_time = int(time.time())

            # Определяем статус
            if spam_protection.cooldown_minutes > 0:
                time_diff = current_time - last_review_time
                cooldown_seconds = spam_protection.cooldown_minutes * 60

                if time_diff < cooldown_seconds:
                    remaining_minutes = (cooldown_seconds - time_diff) // 60
                    status = MSG_USER_STATUS_WAITING.format(remaining_minutes=remaining_minutes)
                    time_until_next = f"{remaining_minutes} мин"
                else:
                    status = MSG_USER_STATUS_READY
                    time_until_next = "Готов"
            else:
                status = MSG_USER_STATUS_READY
                time_until_next = "Готов"

            return {
                'last_review_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_review_time)),
                'reviews_today': reviews_today,
                'time_until_next': time_until_next,
                'status': status
            }

    return None
