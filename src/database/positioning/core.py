"""
Основной модуль позиционирования элементов меню.

Предоставляет класс PositioningManager для управления позициями и группировкой элементов.
Все низкоуровневые функции доступны через отдельные модули.
"""

import logging
from typing import Optional, List, Dict, Tuple
from .position_utils import get_next_position, get_button_groups, get_ordered_items
from .move_operations import move_button_up, move_button_down, move_group_up, move_group_down
from .group_operations import group_buttons, ungroup_buttons
from .validation import can_move_up_new, can_move_down_new, is_item_in_group

logger = logging.getLogger(__name__)


class PositioningManager:
    """
    Менеджер для управления позиционированием элементов меню.

    Предоставляет высокоуровневый интерфейс для всех операций с позициями.
    """

    def __init__(self, parent_id: Optional[int] = None):
        """
        Инициализация менеджера.

        Args:
            parent_id: ID родительского элемента (None для корневого уровня)
        """
        self.parent_id = parent_id

    def get_next_position(self) -> int:
        """Получить следующую доступную позицию."""
        return get_next_position(self.parent_id)

    def move_up(self, item_id: int) -> bool:
        """Переместить элемент вверх."""
        return move_button_up(item_id)

    def move_down(self, item_id: int) -> bool:
        """Переместить элемент вниз."""
        return move_button_down(item_id)

    def move_group_up(self, group_position: int) -> Optional[int]:
        """Переместить группу вверх."""
        return move_group_up(group_position, self.parent_id)

    def move_group_down(self, group_position: int) -> Optional[int]:
        """Переместить группу вниз."""
        return move_group_down(group_position, self.parent_id)

    def group_items(self, item1_id: int, item2_id: int) -> bool:
        """Сгруппировать два элемента."""
        return group_buttons(item1_id, item2_id)

    def ungroup_items(self, group_position: int) -> bool:
        """Разгруппировать элементы в позиции."""
        return ungroup_buttons(group_position, self.parent_id)

    def get_groups(self) -> List[Tuple[int, List[int]]]:
        """Получить список всех групп."""
        return get_button_groups(self.parent_id)

    def get_ordered_list(self) -> List[Dict]:
        """Получить упорядоченный список элементов."""
        return get_ordered_items(self.parent_id)

    def can_move_up(self, item_id: int) -> bool:
        """Проверить, можно ли переместить элемент вверх."""
        return can_move_up_new(item_id)

    def can_move_down(self, item_id: int) -> bool:
        """Проверить, можно ли переместить элемент вниз."""
        return can_move_down_new(item_id)

    def is_in_group(self, item_id: int) -> Optional[Tuple[int, int]]:
        """Проверить, находится ли элемент в группе."""
        return is_item_in_group(item_id)
