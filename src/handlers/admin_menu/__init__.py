"""
Модуль административного меню

Содержит функциональность для управления меню через админ-панель:
- Добавление пунктов меню
- Редактирование существующих пунктов
- Удаление пунктов меню
- Очистка чата
- Отмена операций
- Административная панель
"""

import asyncio
from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from src.handlers.common.utils import is_admin, safe_delete_message, show_main_menu_for_callback
from src.keyboards.keyboards_admin import admin_keyboard
from src.config.config import get_image_path
from src.database import update_admin_info
from src.utils.texts import *
from src.handlers.user_interface.review_ui.review_admin import register_review_admin_handlers
from src.handlers.user_interface.review_ui.review_settings import register_review_settings_handlers
from src.handlers.user_interface.review_ui.review_user_management import register_review_user_management_handlers

from .admin_add import register_admin_add
from .admin_cancel import register_admin_cancel
from .admin_clear import register_admin_clear
from .admin_delete import register_admin_delete
from .admin_edit import register_admin_edit
from .admin_menu import register_admin_menu_handlers
from .admin_stats import register_stats_handlers

__all__ = [
    'register_admin_add',
    'register_admin_cancel',
    'register_admin_clear',
    'register_admin_delete',
    'register_admin_edit',
    'register_admin_menu_handlers',
    'register_stats_handlers',
    'register_all_admin_handlers'
]


def register_all_admin_handlers(dp, bot):
    """Регистрация всех обработчиков админ-меню"""

    # Регистрируем обработчики для системы отзывов
    register_review_admin_handlers(dp)
    register_review_settings_handlers(dp)
    register_review_user_management_handlers(dp)

    # Регистрируем основные админ-обработчики
    register_admin_menu_handlers(dp, bot)

    # Регистрируем остальные обработчики
    register_admin_add(dp)
    register_admin_cancel(dp)
    register_admin_clear(dp, bot)
    register_admin_delete(dp)
    register_admin_edit(dp)
    register_stats_handlers(dp)
