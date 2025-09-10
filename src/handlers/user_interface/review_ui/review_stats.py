"""Статистика и аналитика системы отзывов"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.database.base import get_db
from src.handlers.user_interface.review_logic.review_spam_protection import spam_protection


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

    text = f"""<b>📊 Статистика отзывов</b>

👥 Пользователей с лимитами: {total_users}
📝 Отзывов сегодня: {today_reviews}
🚫 Достигли дневного лимита: {users_at_limit}

<b>Настройки защиты:</b>
⏰ Cooldown: {"отключен" if spam_protection.cooldown_minutes == 0 else f"{spam_protection.cooldown_minutes} мин"}
📊 Лимит в день: {spam_protection.max_reviews_per_day} отзывов

Выберите действие:"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Проверить", callback_data="check_user_reviews"),
             InlineKeyboardButton(text="🔄 Сбросить", callback_data="reset_review_limits")],
            [InlineKeyboardButton(text="⚙️ Изменить настройки", callback_data="configure_review_settings")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_settings")]
        ]
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
