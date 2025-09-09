"""Модуль для получения статистики по меню"""

from typing import Dict, Any
from ..base import get_db

def get_menu_stats() -> Dict[str, Any]:
    """Получает статистику по меню"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM menu")
        total = c.fetchone()[0]

        c.execute("SELECT content_type, COUNT(*) FROM menu GROUP BY content_type")
        types = dict(c.fetchall())

        return {'total_items': total, 'by_type': types}

def get_menu_statistics() -> Dict[str, int]:
    """Получение статистики по меню"""
    with get_db() as conn:
        c = conn.cursor()

        stats = {}

        # Общее количество элементов
        c.execute("SELECT COUNT(*) FROM menu")
        stats['total_items'] = c.fetchone()[0]

        # Количество элементов по типам контента
        c.execute("SELECT content_type, COUNT(*) FROM menu GROUP BY content_type")
        for content_type, count in c.fetchall():
            stats[f'{content_type}_items'] = count

        # Количество корневых элементов
        c.execute("SELECT COUNT(*) FROM menu WHERE parent_id IS NULL")
        stats['root_items'] = c.fetchone()[0]

        # Максимальная глубина вложенности
        c.execute('''WITH RECURSIVE menu_depth(id, depth) AS (
                       SELECT id, 0 FROM menu WHERE parent_id IS NULL
                       UNION ALL
                       SELECT m.id, md.depth + 1
                       FROM menu m
                       JOIN menu_depth md ON m.parent_id = md.id
                     )
                     SELECT MAX(depth) FROM menu_depth''')
        result = c.fetchone()[0]
        stats['max_depth'] = result if result is not None else 0

        return stats
