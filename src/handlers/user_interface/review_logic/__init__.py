"""
Модуль логики обработки отзывов

Содержит основную бизнес-логику для работы с отзывами:
- Защита от спама
- Обработка отзывов
- Вспомогательные функции
- Отправка email
"""

from .review_spam_protection import spam_protection
from .review_handler import register_review_handlers, show_review_form
from .review_utils import (
    review_state_manager,
    show_success_with_timer,
    validate_review_text,
    get_user_info
)
from .review_email import send_review_email

__all__ = [
    'spam_protection',
    'register_review_handlers',
    'show_review_form',
    'review_state_manager',
    'show_success_with_timer',
    'validate_review_text',
    'get_user_info',
    'send_review_email'
]
