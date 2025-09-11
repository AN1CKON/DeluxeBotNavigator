"""Админ-функционал для управления системой отзывов"""

import asyncio
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.handlers.common.utils import is_admin, safe_delete_message
from src.database import update_admin_info
from src.database.base import get_db
from src.utils.texts import NO_ACCESS_MESSAGE, CALLBACK_MANAGE_REVIEWS
from src.models import AdminStates
from src.handlers.user_interface.review_logic.review_spam_protection import spam_protection
from src.handlers.user_interface.review_ui.review_stats import show_reviews_management
from src.handlers.user_interface.review_ui.review_settings_cooldown import show_review_settings_menu


def register_review_admin_handlers(dp):
    """Регистрация всех админ-обработчиков для системы отзывов"""

    @dp.callback_query(F.data == CALLBACK_MANAGE_REVIEWS)
    async def manage_reviews_callback(callback: types.CallbackQuery):
        """Обработчик управления отзывами"""
        if not is_admin(callback.from_user.id):
            try:
                return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
            except Exception:
                return

        await safe_delete_message(callback.message)
        await show_reviews_management(callback.message)

    @dp.callback_query(F.data == "configure_review_settings")
    async def configure_review_settings_callback(callback: types.CallbackQuery):
        """Обработчик изменения настроек защиты от спама"""
        if not is_admin(callback.from_user.id):
            try:
                return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
            except Exception:
                return

        await safe_delete_message(callback.message)
        await show_review_settings_menu(callback.message)

    @dp.callback_query(F.data == "reset_review_limits")
    async def reset_review_limits_callback(callback: types.CallbackQuery):
        """Обработчик сброса лимитов отзывов"""
        if not is_admin(callback.from_user.id):
            try:
                return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
            except Exception:
                return

        # Сбрасываем все лимиты
        with get_db() as conn:
            c = conn.cursor()
            c.execute("UPDATE user_review_limits SET reviews_today = 0, last_reset_date = date('now')")
            conn.commit()

        try:
            await callback.answer("✅ Лимиты отзывов сброшены для всех пользователей", show_alert=True)
        except Exception:
            pass
        await safe_delete_message(callback.message)
        await show_reviews_management(callback.message)

    @dp.callback_query(F.data == "check_user_reviews")
    async def check_user_reviews_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработчик проверки отзывов пользователя"""
        if not is_admin(callback.from_user.id):
            try:
                return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
            except Exception:
                return

        await safe_delete_message(callback.message)
        await callback.message.answer(
            "👤 Введите ID пользователя для проверки статистики отзывов:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=CALLBACK_MANAGE_REVIEWS)]]
            )
        )
        await state.set_state(AdminStates.waiting_for_user_id)
