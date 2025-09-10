"""Управление пользователями и их лимитами в системе отзывов"""

import time
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.handlers.common.utils import is_admin, safe_delete_message
from src.models import AdminStates
from src.utils.texts import NO_ACCESS_MESSAGE
from src.database.base import get_db
from src.handlers.user_interface.review_logic.review_spam_protection import spam_protection


def register_review_user_management_handlers(dp):
    """Регистрация обработчиков для управления пользователями отзывов"""

    @dp.callback_query(F.data == "check_user_reviews")
    async def check_user_reviews_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработчик проверки отзывов пользователя"""
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)

        await safe_delete_message(callback.message)
        await callback.message.answer(
            "👤 Введите ID пользователя для проверки статистики отзывов:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="manage_reviews")]]
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
                text = f"""<b>👤 Статистика пользователя {user_id}</b>

📅 Последний отзыв: {user_stats['last_review_time']}
📊 Отзывов сегодня: {user_stats['reviews_today']}
⏰ Время до следующего отзыва: {user_stats['time_until_next']}

<b>Статус:</b> {user_stats['status']}"""
            else:
                text = f"👤 Пользователь {user_id} еще не оставлял отзывы"

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Сбросить лимиты", callback_data=f"reset_user_limits_{user_id}")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="manage_reviews")]
                ]
            )

            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

        except ValueError:
            await message.answer(
                "❌ Введите корректный ID пользователя (число)",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="manage_reviews")]]
                )
            )
            return

        await state.clear()

    @dp.callback_query(F.data.startswith("reset_user_limits_"))
    async def reset_user_limits_callback(callback: types.CallbackQuery):
        """Обработчик сброса лимитов конкретного пользователя"""
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)

        user_id = int(callback.data.split("_")[3])

        # Сбрасываем лимиты пользователя
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE user_review_limits
                SET reviews_today = 0, last_reset_date = date('now')
                WHERE user_id = ?
            """, (user_id,))
            conn.commit()

        await callback.answer(f"✅ Лимиты пользователя {user_id} сброшены", show_alert=True)
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
                    status = f"⏰ Ожидает {remaining_minutes} мин"
                    time_until_next = f"{remaining_minutes} мин"
                else:
                    status = "✅ Готов к отзыву"
                    time_until_next = "Готов"
            else:
                status = "✅ Готов к отзыву"
                time_until_next = "Готов"

            return {
                'last_review_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_review_time)),
                'reviews_today': reviews_today,
                'time_until_next': time_until_next,
                'status': status
            }

    return None
