"""
Функции валидации и проверки состояния элементов меню.
"""

from typing import Optional, Tuple
from .helpers import get_item_info, get_adjacent_position


def can_move_up_new(item_id: int) -> bool:
    """
    Проверяет, можно ли переместить элемент или группу вверх.

    Args:
        item_id: ID элемента

    Returns:
        True если можно переместить вверх
    """
    item_info = get_item_info(item_id)
    if not item_info:
        return False

    position, parent_id = item_info
    return get_adjacent_position(position, 'up', parent_id) is not None


def can_move_down_new(item_id: int) -> bool:
    """
    Проверяет, можно ли переместить элемент или группу вниз.

    Args:
        item_id: ID элемента

    Returns:
        True если можно переместить вниз
    """
    item_info = get_item_info(item_id)
    if not item_info:
        return False

    position, parent_id = item_info
    return get_adjacent_position(position, 'down', parent_id) is not None


def is_item_in_group(item_id: int) -> Optional[Tuple[int, int]]:
    """
    Проверяет, входит ли элемент в группу (position-based).

    Args:
        item_id: ID элемента для проверки

    Returns:
        Кортеж (item1_id, item2_id) если элемент в группе, иначе None
    """
    from .helpers import get_items_at_position

    item_info = get_item_info(item_id)
    if not item_info:
        return None

    position, parent_id = item_info
    items_at_position = get_items_at_position(position, parent_id)

    if len(items_at_position) != 2:
        return None  # Не группа или больше 2 элементов

    # Возвращаем IDs в правильном порядке
    item1_id_db, item2_id_db = items_at_position

    # Убеждаемся, что наш элемент один из них
    if item_id not in (item1_id_db, item2_id_db):
        return None

    return (item1_id_db, item2_id_db)