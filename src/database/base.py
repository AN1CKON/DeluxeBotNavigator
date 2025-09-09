"""Базовый модуль для работы с базой данных SQLite"""

import os
import sqlite3
import logging
from typing import Optional
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
        entities TEXT,
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
    
    ADMINS_TABLE_SQL = '''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        added_by INTEGER,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_super_admin BOOLEAN DEFAULT FALSE,
        FOREIGN KEY(added_by) REFERENCES admins(user_id)
    )'''
    
    PLUGIN_STATS_TABLE_SQL = '''CREATE TABLE IF NOT EXISTS plugin_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL CHECK(status IN ('актуален', 'на обновлении')),
        progress INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )'''
    
    # Колонки для добавления в таблицу menu (если их нет)
    MENU_COLUMNS_TO_ADD = [
        ('updated_at', 'DATETIME'),
        ('created_at', 'DATETIME'), 
        ('position', 'INTEGER'),
        ('image_path', 'TEXT'),
        ('entities', 'TEXT')
    ]
    
    try:
        with get_db() as conn:
            c = conn.cursor()
            
            # Создаем таблицы
            c.execute(MENU_TABLE_SQL)
            c.execute(USERS_TABLE_SQL)
            c.execute(ADMINS_TABLE_SQL)
            c.execute(PLUGIN_STATS_TABLE_SQL)
            
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

def _get_next_position(parent_id: Optional[int]) -> int:
    """Получает следующую позицию для нового элемента меню (новый алгоритм)"""
    from .positioning.core import get_next_position
    return get_next_position(parent_id)
