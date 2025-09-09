"""
Модуль позиционирования элементов меню

Этот модуль предоставляет чистый API для работы с позициями и группировкой
элементов меню. Функции разделены по модулям для лучшей организации.
"""

from .core import PositioningManager
from .position_utils import get_next_position, get_button_groups, get_ordered_items
from .move_operations import move_button_up, move_button_down, move_group_up, move_group_down
from .group_operations import group_buttons, ungroup_buttons
from .validation import can_move_up_new, can_move_down_new, is_item_in_group
from .helpers import get_item_info, get_items_at_position, get_max_position, get_adjacent_position, update_positions

__all__ = [
    # Основной класс
    'PositioningManager',

    # Утилиты позиций
    'get_next_position',
    'get_button_groups',
    'get_ordered_items',

    # Операции перемещения
    'move_button_up',
    'move_button_down',
    'move_group_up',
    'move_group_down',

    # Операции группировки
    'group_buttons',
    'ungroup_buttons',

    # Валидация
    'can_move_up_new',
    'can_move_down_new',
    'is_item_in_group',

    # Вспомогательные функции (для продвинутого использования)
    'get_item_info',
    'get_items_at_position',
    'get_max_position',
    'get_adjacent_position',
    'update_positions'
]
