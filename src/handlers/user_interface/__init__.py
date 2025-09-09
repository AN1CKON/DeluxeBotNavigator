"""
Модуль пользовательского интерфейса

Содержит функциональность для взаимодействия с пользователями:
- Стартовая команда и главное меню
- Приветствие новых пользователей
- Навигация по меню
"""

from .start import register_start
from .welcome import register_welcome
from .navigation import register_navigation

__all__ = [
    'register_start',
    'register_welcome',
    'register_navigation'
]
