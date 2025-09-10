"""
Модуль пользовательского интерфейса

Содержит функциональность для взаимодействия с пользователями:
- Стартовая команда и главное меню
- Приветствие новых пользователей
- Навигация по меню
- Система отзывов (разделена на логику и UI)
"""

from .start import register_start
from .welcome import register_welcome
from .navigation import register_navigation

# Импорты из логики отзывов
from .review_logic import (
    spam_protection,
    register_review_handlers,
    show_review_form,
    review_state_manager,
    show_success_with_timer,
    validate_review_text,
    get_user_info,
    send_review_email
)

# Импорты из UI отзывов
from .review_ui import (
    register_review_admin_handlers,
    register_review_settings_handlers,
    register_review_user_management_handlers,
    show_reviews_management,
    create_rating_keyboard,
    create_review_form_keyboard,
    get_rating_description,
    REVIEW_STATES,
    # Текстовые константы
    MSG_REVIEW_RATING,
    MSG_REVIEW_FORM,
    MSG_REVIEW_SUCCESS,
    MSG_REVIEW_SUCCESS_WITH_TIMER,
    MSG_REVIEW_ERROR,
    MSG_REVIEW_TOO_SHORT,
    MSG_REVIEW_TOO_LONG
)

__all__ = [
    'register_start',
    'register_welcome',
    'register_navigation',
    # Логика отзывов
    'spam_protection',
    'register_review_handlers',
    'show_review_form',
    'review_state_manager',
    'show_success_with_timer',
    'validate_review_text',
    'get_user_info',
    'send_review_email',
    # UI отзывов
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
