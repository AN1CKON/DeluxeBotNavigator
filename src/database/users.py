"""Модуль для работы с пользователями в базе данных"""

import logging
from typing import List, Dict, Optional
from .base import get_db

logger = logging.getLogger(__name__)

def add_user(user_id: int, username: Optional[str] = None, 
             first_name: Optional[str] = None) -> bool:
    """Добавление пользователя"""
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO users (user_id, username, first_name) 
                         VALUES (?, ?, ?)''',
                      (user_id, username, first_name))
            conn.commit()
            logger.info(f"👤 Добавлен пользователь: {username or first_name or user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления пользователя {user_id}: {e}")
            return False

def get_user(user_id: int) -> Optional[Dict]:
    """Получение информации о пользователе"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        return dict(result) if result else None

def update_user_visit(user_id: int) -> None:
    """Обновление времени последнего визита пользователя"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET last_visit = datetime('now') WHERE user_id = ?", 
                  (user_id,))
        conn.commit()

def set_welcome_shown(user_id: int) -> None:
    """Отметка показа приветствия пользователю"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET welcome_shown = TRUE WHERE user_id = ?", 
                  (user_id,))
        conn.commit()

def is_welcome_shown(user_id: int) -> bool:
    """Проверка, показывалось ли приветствие пользователю"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT welcome_shown FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        return bool(result and result[0]) if result else False

def get_all_users() -> List[Dict]:
    """Получение всех пользователей"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users ORDER BY first_visit DESC")
        return [dict(row) for row in c.fetchall()]

def get_users_count() -> int:
    """Получение количества пользователей"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        return c.fetchone()[0]

def delete_user(user_id: int) -> bool:
    """Удаление пользователя"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        deleted = c.rowcount > 0
        if deleted:
            conn.commit()
            logger.info(f"🗑️ Удален пользователь ID: {user_id}")
        return deleted

def user_exists(user_id: int) -> bool:
    """Проверка существования пользователя"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        return c.fetchone() is not None

def update_user_info(user_id: int, username: Optional[str] = None, 
                    first_name: Optional[str] = None) -> bool:
    """Обновление информации о пользователе"""
    updates = []
    params = []
    
    if username is not None:
        updates.append("username = ?")
        params.append(username)
    
    if first_name is not None:
        updates.append("first_name = ?")
        params.append(first_name)
    
    if not updates:
        return False
    
    params.append(user_id)
    
    with get_db() as conn:
        c = conn.cursor()
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
        c.execute(query, params)
        updated = c.rowcount > 0
        if updated:
            conn.commit()
            logger.info(f"📝 Обновлена информация пользователя ID: {user_id}")
        return updated

def is_new_user(user_id: int) -> bool:
    """Проверяет, является ли пользователь новым"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT welcome_shown FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        
        is_new = result is None or not bool(result[0])
        logger.info(f"🔍 Пользователь {user_id}: новый = {is_new}")
        return is_new

def register_user(user_id: int, username: Optional[str] = None, 
                 first_name: Optional[str] = None) -> bool:
    """Регистрирует нового пользователя или обновляет информацию"""
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

def mark_welcome_shown(user_id: int) -> bool:
    """Отмечает показ приветствия пользователю"""
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

def get_users_statistics() -> Dict[str, int]:
    """Получение статистики по пользователям"""
    with get_db() as conn:
        c = conn.cursor()
        
        stats = {}
        
        # Общее количество пользователей
        c.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = c.fetchone()[0]
        
        # Пользователи, которым показывалось приветствие
        c.execute("SELECT COUNT(*) FROM users WHERE welcome_shown = TRUE")
        stats['welcomed_users'] = c.fetchone()[0]
        
        # Новые пользователи (последние 24 часа)
        c.execute('''SELECT COUNT(*) FROM users 
                     WHERE first_visit > datetime('now', '-1 day')''')
        stats['new_users_24h'] = c.fetchone()[0]
        
        # Активные пользователи (последние 7 дней)
        c.execute('''SELECT COUNT(*) FROM users 
                     WHERE last_visit > datetime('now', '-7 days')''')
        stats['active_users_7d'] = c.fetchone()[0]
        
        return stats
