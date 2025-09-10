"""Модуль для CRUD операций с элементами меню"""

import sqlite3
import logging
from typing import Optional
from src.database.base import get_db, _get_next_position

logger = logging.getLogger(__name__)

def add_menu_item(parent_id: Optional[int], title: str, content: str,
                 content_type: str, image_path: Optional[str] = None,
                 entities: Optional[str] = None, position: Optional[int] = None) -> int:
    """Добавление элемента меню"""
    with get_db() as conn:
        c = conn.cursor()

        actual_position = position if position is not None else _get_next_position(parent_id)

        c.execute('''INSERT INTO menu
                     (parent_id, title, content, content_type, position, image_path, entities)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (parent_id, title, content, content_type, actual_position, image_path, entities))
        conn.commit()
        item_id = c.lastrowid
        logger.info(f"➕ Добавлен элемент меню: {title} (ID: {item_id})")
        return item_id

def delete_menu_item(item_id: int) -> bool:
    """Удаление элемента меню"""
    with get_db() as conn:
        c = conn.cursor()

        # Получаем информацию об элементе перед удалением
        c.execute("SELECT title, parent_id FROM menu WHERE id = ?", (item_id,))
        item_info = c.fetchone()
        if not item_info:
            logger.warning(f"⚠️ Элемент с ID {item_id} не найден")
            return False

        title, parent_id = item_info

        # Удаляем элемент (каскадное удаление дочерних элементов)
        c.execute("DELETE FROM menu WHERE id = ?", (item_id,))
        deleted_count = c.rowcount

        if deleted_count > 0:
            # Обновляем позиции оставшихся элементов
            _update_positions_after_delete(conn, parent_id, item_id)
            conn.commit()
            logger.info(f"🗑️ Удален элемент меню: {title} (ID: {item_id})")
            return True
        return False

def update_menu_item(item_id: int, **kwargs) -> bool:
    """Обновление элемента меню"""
    if not kwargs:
        return False

    with get_db() as conn:
        c = conn.cursor()

        # Формируем SQL запрос
        columns = []
        values = []
        for column, value in kwargs.items():
            columns.append(f"{column} = ?")
            values.append(value)

        columns.append("updated_at = datetime('now')")
        values.append(item_id)

        query = f"UPDATE menu SET {', '.join(columns)} WHERE id = ?"
        c.execute(query, values)

        updated = c.rowcount > 0
        if updated:
            conn.commit()
            logger.info(f"📝 Обновлен элемент меню ID: {item_id}")
        return updated

def clear_all_menu() -> None:
    """Очистка всех элементов меню"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM menu")
        conn.commit()
        logger.info("🗑️ Все элементы меню удалены")

def _update_positions_after_delete(conn: sqlite3.Connection, parent_id: Optional[int], deleted_id: int) -> None:
    """Обновление позиций после удаления элемента"""
    c = conn.cursor()

    # Получаем позицию удаленного элемента
    c.execute("SELECT position FROM menu WHERE id = ?", (deleted_id,))
    result = c.fetchone()
    if not result:
        return

    deleted_position = result[0]

    # Сдвигаем позиции элементов, которые шли после удаленного
    query = "UPDATE menu SET position = position - 1 WHERE parent_id "
    if parent_id is None:
        query += "IS NULL AND position > ?"
        params = (deleted_position,)
    else:
        query += "= ? AND position > ?"
        params = (parent_id, deleted_position)

    c.execute(query, params)
