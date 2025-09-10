"""
Вспомогательные функции для работы с базой данных позиционирования.
"""

import logging
from typing import Optional, List, Tuple
from src.database.base import get_db

logger = logging.getLogger(__name__)


def get_item_info(item_id: int) -> Optional[Tuple[int, Optional[int]]]:
    """
    Получить позицию и parent_id элемента.

    Args:
        item_id: ID элемента

    Returns:
        Кортеж (position, parent_id) или None если элемент не найден
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT position, parent_id FROM menu WHERE id = ?", (item_id,))
        result = c.fetchone()
        return result if result else None


def get_items_at_position(position: int, parent_id: Optional[int] = None) -> List[int]:
    """
    Получить список ID элементов на заданной позиции.

    Args:
        position: Позиция
        parent_id: ID родительского элемента

    Returns:
        Список ID элементов
    """
    with get_db() as conn:
        c = conn.cursor()
        if parent_id is None:
            c.execute("SELECT id FROM menu WHERE parent_id IS NULL AND position = ? ORDER BY updated_at ASC", (position,))
        else:
            c.execute("SELECT id FROM menu WHERE parent_id = ? AND position = ? ORDER BY updated_at ASC", (parent_id, position))

        return [row[0] for row in c.fetchall()]


def get_max_position(parent_id: Optional[int] = None) -> int:
    """
    Получить максимальную позицию для заданного parent_id.

    Args:
        parent_id: ID родительского элемента

    Returns:
        Максимальная позиция
    """
    with get_db() as conn:
        c = conn.cursor()
        if parent_id is None:
            c.execute("SELECT COALESCE(MAX(position), 0) FROM menu WHERE parent_id IS NULL")
        else:
            c.execute("SELECT COALESCE(MAX(position), 0) FROM menu WHERE parent_id = ?", (parent_id,))

        result = c.fetchone()
        return result[0] if result else 0


def get_adjacent_position(current_position: int, direction: str, parent_id: Optional[int] = None) -> Optional[int]:
    """
    Получить соседнюю позицию (предыдущую или следующую).

    Args:
        current_position: Текущая позиция
        direction: 'up' или 'down'
        parent_id: ID родительского элемента

    Returns:
        Соседняя позиция или None если её нет
    """
    with get_db() as conn:
        c = conn.cursor()

        if direction == 'up':
            order = "DESC"
            operator = "<"
        elif direction == 'down':
            order = "ASC"
            operator = ">"
        else:
            raise ValueError("Direction must be 'up' or 'down'")

        if parent_id is None:
            c.execute(f"""
                SELECT position FROM menu
                WHERE parent_id IS NULL AND position {operator} ?
                ORDER BY position {order} LIMIT 1
            """, (current_position,))
        else:
            c.execute(f"""
                SELECT position FROM menu
                WHERE parent_id = ? AND position {operator} ?
                ORDER BY position {order} LIMIT 1
            """, (parent_id, current_position))

        result = c.fetchone()
        return result[0] if result else None


def update_positions(updates: List[Tuple[int, int]], parent_id: Optional[int] = None) -> None:
    """
    Обновить позиции нескольких элементов.

    Args:
        updates: Список кортежей (item_id, new_position)
        parent_id: ID родительского элемента (для логирования)
    """
    with get_db() as conn:
        c = conn.cursor()
        for item_id, new_position in updates:
            c.execute("UPDATE menu SET position = ? WHERE id = ?", (new_position, item_id))
            logger.debug(f"Обновлена позиция элемента {item_id} на {new_position} (parent_id: {parent_id})")
        conn.commit()
