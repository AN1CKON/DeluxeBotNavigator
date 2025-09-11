"""Статистика и аналитика системы отзывов"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.database.base import get_db
from src.handlers.user_interface.review_logic.review_spam_protection import spam_protection
from src.utils.texts import (
    MSG_REVIEW_STATS_MENU,
    BUTTON_CHECK_USER,
    BUTTON_RESET_LIMITS,
    BUTTON_CONFIGURE_SETTINGS,
    BUTTON_BACK,
    CALLBACK_ADMIN_SETTINGS
)


async def show_reviews_management(message):
    """Показывает меню управления отзывами для администраторов"""
    # Получаем статистику по отзывам
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM user_review_limits")
        total_users = c.fetchone()[0]

        c.execute("SELECT SUM(reviews_today) FROM user_review_limits WHERE last_reset_date = date('now')")
        today_reviews = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM user_review_limits WHERE reviews_today >= ?", (spam_protection.max_reviews_per_day,))
        users_at_limit = c.fetchone()[0]

    text = MSG_REVIEW_STATS_MENU.format(
        total_users=total_users,
        today_reviews=today_reviews,
        users_at_limit=users_at_limit,
        cooldown_status="отключен" if spam_protection.cooldown_minutes == 0 else f"{spam_protection.cooldown_minutes} мин",
        max_reviews=spam_protection.max_reviews_per_day
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BUTTON_CHECK_USER, callback_data="check_user_reviews"),
             InlineKeyboardButton(text=BUTTON_RESET_LIMITS, callback_data="reset_review_limits")],
            [InlineKeyboardButton(text=BUTTON_CONFIGURE_SETTINGS, callback_data="configure_review_settings")],
            [InlineKeyboardButton(text=BUTTON_BACK, callback_data=CALLBACK_ADMIN_SETTINGS)]
        ]
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
