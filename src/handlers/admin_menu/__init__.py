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

from .admin_add import register_admin_add
from .admin_cancel import register_admin_cancel  
from .admin_clear import register_admin_clear
from .admin_delete import register_admin_delete
from .admin_edit import register_admin_edit
from .admin_menu import register_admin_menu
from .admin_stats import register_stats_handlers

__all__ = [
    'register_admin_add',
    'register_admin_cancel', 
    'register_admin_clear',
    'register_admin_delete',
    'register_admin_edit',
    'register_admin_menu',
    'register_stats_handlers'
]
