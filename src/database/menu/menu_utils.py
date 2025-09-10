"""Модуль с утилитарными функциями для работы с меню"""

import logging
from typing import List, Dict, Optional
from src.database.base import get_db

logger = logging.getLogger(__name__)

def has_children(item_id: int) -> bool:
    """Проверяет наличие дочерних пунктов у элемента"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT EXISTS(SELECT 1 FROM menu WHERE parent_id = ?)", (item_id,))
        return bool(c.fetchone()[0])

def change_menu_position(item_id: int, new_position: int) -> bool:
    """Изменяет позицию пункта меню"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE menu SET position = ?, updated_at = datetime('now') WHERE id = ?",
                 (new_position, item_id))
        conn.commit()
        success = c.rowcount > 0
        if success:
            logger.info(f"🔄 Изменена позиция пункта меню ID: {item_id}")
        return success

def update_menu_item_image(item_id: int, image_path: Optional[str] = None) -> bool:
    """Обновляет изображение пункта меню"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE menu
            SET image_path = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (image_path, item_id))
        conn.commit()
        success = c.rowcount > 0
        if success:
            logger.info(f"🖼️ Обновлено изображение пункта меню ID: {item_id}")
        return success

def check_menu_item_exists(item_id: int) -> bool:
    """Проверка существования элемента меню"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM menu WHERE id = ?", (item_id,))
        return c.fetchone() is not None

def get_menu_path(item_id: int) -> List[Dict]:
    """Получение пути к элементу меню (от корня)"""
    path = []
    current_id = item_id

    with get_db() as conn:
        c = conn.cursor()

        while current_id is not None:
            c.execute("SELECT id, title, parent_id FROM menu WHERE id = ?", (current_id,))
            item = c.fetchone()
            if item:
                path.insert(0, dict(item))
                current_id = item['parent_id']
            else:
                break

    return path

def search_menu_items(search_term: str) -> List[Dict]:
    """Поиск элементов меню по заголовку или содержимому"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT * FROM menu
                     WHERE title LIKE ? OR content LIKE ?
                     ORDER BY title''',
                  (f'%{search_term}%', f'%{search_term}%'))
        return [dict(row) for row in c.fetchall()]
