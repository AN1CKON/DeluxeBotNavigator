"""Модуль для управления администраторами"""

import logging
from typing import Optional
from src.database.base import get_db

logger = logging.getLogger(__name__)

def promote_to_super_admin(user_id: int) -> bool:
    """Повышение администратора до суперадминистратора"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE admins SET is_super_admin = TRUE WHERE user_id = ?",
                  (user_id,))
        updated = c.rowcount > 0
        if updated:
            conn.commit()
            logger.info(f"⬆️ Пользователь {user_id} повышен до суперадминистратора")
        return updated

def demote_from_super_admin(user_id: int) -> bool:
    """Понижение суперадминистратора до обычного администратора"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE admins SET is_super_admin = FALSE WHERE user_id = ?",
                  (user_id,))
        updated = c.rowcount > 0
        if updated:
            conn.commit()
            logger.info(f"⬇️ Пользователь {user_id} понижен до обычного администратора")
        return updated

def init_super_admin(user_id: int, username: Optional[str] = None,
                    first_name: Optional[str] = None) -> bool:
    """Инициализирует супер-администратора при первом запуске"""
    with get_db() as conn:
        c = conn.cursor()
        # Проверяем, есть ли уже супер-админ
        c.execute("SELECT COUNT(*) FROM admins WHERE is_super_admin = 1")
        if c.fetchone()[0] > 0:
            return True  # Супер-админ уже существует

        # Добавляем супер-администратора
        c.execute("""
            INSERT OR REPLACE INTO admins
            (user_id, username, first_name, added_by, is_super_admin)
            VALUES (?, ?, ?, ?, 1)
        """, (user_id, username, first_name, user_id))

        conn.commit()
        logger.info(f"👑 Супер-администратор инициализирован: {user_id} (@{username})")
        return True
