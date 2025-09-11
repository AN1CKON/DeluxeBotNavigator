"""
Модуль пользовательского интерфейса отзывов

Содержит компоненты пользовательского интерфейса для работы с отзывами:
- Админ-панель управления отзывами
- Настройки системы защиты
- Управление пользователями
- Статистика и аналитика
- Клавиатуры и константы
"""

from .review_admin import register_review_admin_handlers
from .review_settings_cooldown import register_cooldown_handlers, register_reset_handlers
from .review_settings_daily import register_daily_limit_handlers, register_cancel_handlers
from .review_user_management import register_review_user_management_handlers
from .review_stats import show_reviews_management
from .review_keyboard import create_rating_keyboard, create_review_form_keyboard, get_rating_description
from .review_constants import REVIEW_STATES

# Импорт текстовых констант из utils
from ....utils.texts import (
    MSG_REVIEW_RATING,
    MSG_REVIEW_FORM,
    MSG_REVIEW_SUCCESS,
    MSG_REVIEW_SUCCESS_WITH_TIMER,
    MSG_REVIEW_ERROR,
    MSG_REVIEW_TOO_SHORT,
    MSG_REVIEW_TOO_LONG
)


def register_review_settings_handlers(dp):
    """Регистрация всех обработчиков для управления настройками защиты от спама"""
    register_cooldown_handlers(dp)
    register_daily_limit_handlers(dp)
    register_reset_handlers(dp)
    register_cancel_handlers(dp)


__all__ = [
    'register_review_admin_handlers',
    'register_review_settings_handlers',
    'register_review_user_management_handlers',
    'show_reviews_management',
    'create_rating_keyboard',
    'create_review_form_keyboard',
    'get_rating_description',
    'REVIEW_STATES',
    # Текстовые константы
    'MSG_REVIEW_RATING',
    'MSG_REVIEW_FORM',
    'MSG_REVIEW_SUCCESS',
    'MSG_REVIEW_SUCCESS_WITH_TIMER',
    'MSG_REVIEW_ERROR',
    'MSG_REVIEW_TOO_SHORT',
    'MSG_REVIEW_TOO_LONG'
]
