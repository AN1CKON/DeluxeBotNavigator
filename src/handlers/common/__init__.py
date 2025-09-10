"""
Модуль общих утилит

Содержит вспомогательные функции общего назначения:
- Проверка прав администратора
- Безопасные операции с сообщениями
- Форматирование данных
- Отображение главного меню
"""

from .utils import *

from .utils import is_admin, is_super_admin, safe_delete_message, format_menu_item_display, show_main_menu_for_callback

__all__ = [
    'is_admin',
    'is_super_admin', 
    'safe_delete_message',
    'format_menu_item_display',
    'show_main_menu_for_callback'
]
