"""
Утилиты для работы с позициями элементов меню.
"""

import logging
from typing import Optional, List, Dict, Tuple
from ..base import get_db

logger = logging.getLogger(__name__)


def get_next_position(parent_id: Optional[int] = None) -> int:
    """
    Получает следующую позицию для нового элемента (максимальный ID + 1).

    Args:
        parent_id: ID родительского элемента (None для корневого уровня)

    Returns:
        Новая позиция для элемента
    """
    with get_db() as conn:
        c = conn.cursor()

        # Ищем максимальную позицию среди всех элементов с таким же parent_id
        if parent_id is None:
            c.execute("SELECT COALESCE(MAX(position), 0) FROM menu WHERE parent_id IS NULL")
        else:
            c.execute("SELECT COALESCE(MAX(position), 0) FROM menu WHERE parent_id = ?", (parent_id,))

        result = c.fetchone()
        max_position = result[0] if result else 0

        return max_position + 1


def get_button_groups(parent_id: Optional[int] = None) -> List[Tuple[int, List[int]]]:
    """
    Возвращает список групп кнопок.

    Args:
        parent_id: ID родительского элемента

    Returns:
        Список кортежей (position, [item_ids]) для каждой группы
    """
    with get_db() as conn:
        c = conn.cursor()

        # Находим позиции, где есть более одной кнопки
        if parent_id is None:
            c.execute("""
                SELECT position, GROUP_CONCAT(id ORDER BY updated_at ASC) as item_ids, COUNT(*) as cnt
                FROM menu
                WHERE parent_id IS NULL
                GROUP BY position
                HAVING COUNT(*) > 1
                ORDER BY position
            """)
        else:
            c.execute("""
                SELECT position, GROUP_CONCAT(id ORDER BY updated_at ASC) as item_ids, COUNT(*) as cnt
                FROM menu
                WHERE parent_id = ?
                GROUP BY position
                HAVING COUNT(*) > 1
                ORDER BY position
            """, (parent_id,))

        groups = []
        for position, item_ids_str, count in c.fetchall():
            item_ids = [int(id_str) for id_str in item_ids_str.split(',')]
            groups.append((position, item_ids))

        return groups


def get_ordered_items(parent_id: Optional[int] = None) -> List[Dict]:
    """
    Возвращает упорядоченный список всех элементов меню с информацией о группировке.

    Args:
        parent_id: ID родительского элемента

    Returns:
        Список словарей с информацией об элементах
    """
    with get_db() as conn:
        c = conn.cursor()

        if parent_id is None:
            c.execute("""
                SELECT id, title, position,
                       (SELECT COUNT(*) FROM menu m2 WHERE m2.parent_id IS NULL AND m2.position = menu.position) as group_size
                FROM menu
                WHERE parent_id IS NULL
                ORDER BY position, updated_at ASC
            """)
        else:
            c.execute("""
                SELECT id, title, position,
                       (SELECT COUNT(*) FROM menu m2 WHERE m2.parent_id = ? AND m2.position = menu.position) as group_size
                FROM menu
                WHERE parent_id = ?
                ORDER BY position, updated_at ASC
            """, (parent_id, parent_id))

        items = []
        for row in c.fetchall():
            items.append({
                'id': row[0],
                'title': row[1],
                'position': row[2],
                'is_grouped': row[3] > 1,
                'group_size': row[3]
            })

        return items
