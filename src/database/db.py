"""Модуль работы с базой данных SQLite"""

import os
import sqlite3
import logging
from typing import Optional, List, Tuple, Dict, Any
from contextlib import contextmanager
from ..config.config import DB_PATH

logger = logging.getLogger(__name__)

@contextmanager
def get_db():
    """Context manager для безопасной работы с базой данных"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"❌ Ошибка базы данных: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """Инициализация базы данных с автоматическим добавлением недостающих колонок"""
    
    # Создаем директорию для базы данных если она не существует
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"📁 Создана директория для БД: {db_dir}")
    
    # SQL запросы для создания таблиц
    MENU_TABLE_SQL = '''CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER,
        title TEXT NOT NULL,
        content TEXT,
        content_type TEXT NOT NULL,
        position INTEGER,
        image_path TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(parent_id) REFERENCES menu(id) ON DELETE CASCADE
    )'''
    
    USERS_TABLE_SQL = '''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        welcome_shown BOOLEAN DEFAULT FALSE,
        first_visit DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_visit DATETIME DEFAULT CURRENT_TIMESTAMP
    )'''
    
    # Колонки для добавления в таблицу menu (если их нет)
    MENU_COLUMNS_TO_ADD = [
        ('updated_at', 'DATETIME'),
        ('created_at', 'DATETIME'), 
        ('position', 'INTEGER'),
        ('image_path', 'TEXT')
    ]
    
    try:
        with get_db() as conn:
            c = conn.cursor()
            
            # Создаем таблицы
            c.execute(MENU_TABLE_SQL)
            c.execute(USERS_TABLE_SQL)
            
            # Проверяем и добавляем недостающие колонки в таблицу menu
            c.execute("PRAGMA table_info(menu)")
            existing_columns = {column[1] for column in c.fetchall()}
            
            for column_name, column_type in MENU_COLUMNS_TO_ADD:
                if column_name not in existing_columns:
                    c.execute(f"ALTER TABLE menu ADD COLUMN {column_name} {column_type}")
                    
                    # Устанавливаем значения по умолчанию для новых колонок
                    if column_name in ('created_at', 'updated_at'):
                        c.execute(f"UPDATE menu SET {column_name} = datetime('now') WHERE {column_name} IS NULL")
                    elif column_name == 'position':
                        c.execute("UPDATE menu SET position = id WHERE position IS NULL")
                    
                    logger.info(f"🔧 Добавлена колонка {column_name} в таблицу menu")
            
            conn.commit()
            logger.info("🗄️ База данных инициализирована успешно")
            
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С МЕНЮ ==========

def _get_next_position(parent_id: Optional[int]) -> int:
    """Получает следующую позицию для нового элемента меню"""
    with get_db() as conn:
        c = conn.cursor()
        query = "SELECT COALESCE(MAX(position), 0) + 1 FROM menu WHERE parent_id " + \
                ("IS NULL" if parent_id is None else "= ?")
        params = () if parent_id is None else (parent_id,)
        c.execute(query, params)
        return c.fetchone()[0]

def add_menu_item(title: str, content: Optional[str], content_type: str, parent_id: Optional[int] = None) -> int:
    """Добавляет новый пункт меню"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            position = _get_next_position(parent_id)
            
            c.execute("""
                INSERT INTO menu (parent_id, title, content, content_type, position, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (parent_id, title, content, content_type, position))
            
            conn.commit()
            item_id = c.lastrowid
            logger.info(f"➕ Добавлен пункт меню: {title} (ID: {item_id})")
            return item_id
            
    except Exception as e:
        logger.error(f"❌ Ошибка добавления пункта меню: {e}")
        raise

def get_menu_items(parent_id: Optional[int] = None) -> List[Tuple[int, str]]:
    """Получает список пунктов меню, отсортированных по позиции"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            query = "SELECT id, title FROM menu WHERE parent_id " + \
                    ("IS NULL" if parent_id is None else "= ?") + " ORDER BY position ASC"
            params = () if parent_id is None else (parent_id,)
            c.execute(query, params)
            return c.fetchall()
    except Exception as e:
        logger.error(f"❌ Ошибка получения пунктов меню: {e}")
        return []

def has_children(item_id: int) -> bool:
    """Проверяет наличие дочерних пунктов у элемента"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT EXISTS(SELECT 1 FROM menu WHERE parent_id = ?)", (item_id,))
            return bool(c.fetchone()[0])
    except Exception as e:
        logger.error(f"❌ Ошибка проверки дочерних элементов: {e}")
        return False

def get_menu_item(item_id: int) -> Optional[sqlite3.Row]:
    """Получает конкретный пункт меню по ID"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM menu WHERE id = ?", (item_id,))
            return c.fetchone()
    except Exception as e:
        logger.error(f"❌ Ошибка получения пункта меню: {e}")
        return None

def update_menu_item(item_id: int, title: str, content: Optional[str], 
                    content_type: str, parent_id: Optional[int] = None) -> bool:
    """Обновляет пункт меню"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE menu 
                SET title = ?, content = ?, content_type = ?, parent_id = ?, updated_at = datetime('now') 
                WHERE id = ?
            """, (title, content, content_type, parent_id, item_id))
            conn.commit()
            success = c.rowcount > 0
            if success:
                logger.info(f"✏️ Обновлён пункт меню ID: {item_id}")
            return success
    except Exception as e:
        logger.error(f"❌ Ошибка обновления пункта меню: {e}")
        return False

def delete_menu_item(item_id: int) -> bool:
    """Удаляет пункт меню"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM menu WHERE id = ?", (item_id,))
            conn.commit()
            success = c.rowcount > 0
            if success:
                logger.info(f"🗑️ Удалён пункт меню ID: {item_id}")
            return success
    except Exception as e:
        logger.error(f"❌ Ошибка удаления пункта меню: {e}")
        return False

def change_menu_position(item_id: int, new_position: int) -> bool:
    """Изменяет позицию пункта меню"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("UPDATE menu SET position = ?, updated_at = datetime('now') WHERE id = ?", 
                     (new_position, item_id))
            conn.commit()
            success = c.rowcount > 0
            if success:
                logger.info(f"🔄 Изменена позиция пункта меню ID: {item_id}")
            return success
    except Exception as e:
        logger.error(f"❌ Ошибка изменения позиции: {e}")
        return False

def update_menu_item_image(item_id: int, image_path: Optional[str] = None) -> bool:
    """Обновляет изображение пункта меню"""
    try:
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
    except Exception as e:
        logger.error(f"❌ Ошибка обновления изображения пункта меню: {e}")
        return False

def get_menu_stats() -> Dict[str, Any]:
    """Получает статистику по меню"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM menu")
            total = c.fetchone()[0]
            
            c.execute("SELECT content_type, COUNT(*) FROM menu GROUP BY content_type")
            types = dict(c.fetchall())
            
            return {'total_items': total, 'by_type': types}
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        return {'total_items': 0, 'by_type': {}}

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==========

def is_new_user(user_id: int) -> bool:
    """Проверяет, является ли пользователь новым"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT welcome_shown FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            
            is_new = result is None or not bool(result[0])
            logger.info(f"🔍 Пользователь {user_id}: новый = {is_new}")
            return is_new
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки нового пользователя: {e}")
        return False

def register_user(user_id: int, username: str = None, first_name: str = None) -> bool:
    """Регистрирует нового пользователя или обновляет информацию"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            
            # Используем INSERT OR REPLACE для упрощения логики
            c.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, welcome_shown, first_visit, last_visit) 
                VALUES (
                    ?, ?, ?, 
                    COALESCE((SELECT welcome_shown FROM users WHERE user_id = ?), FALSE),
                    COALESCE((SELECT first_visit FROM users WHERE user_id = ?), datetime('now')),
                    datetime('now')
                )
            """, (user_id, username, first_name, user_id, user_id))
            
            conn.commit()
            logger.info(f"👤 Пользователь обработан: {user_id} (@{username})")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации пользователя: {e}")
        return False

def mark_welcome_shown(user_id: int) -> bool:
    """Отмечает показ приветствия пользователю"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET welcome_shown = 1 WHERE user_id = ?", (user_id,))
            
            if c.rowcount > 0:
                conn.commit()
                logger.info(f"✅ Приветствие отмечено для пользователя: {user_id}")
                return True
            else:
                logger.warning(f"⚠️ Пользователь {user_id} не найден")
                return False
                
    except Exception as e:
        logger.error(f"❌ Ошибка отметки приветствия: {e}")
        return False
