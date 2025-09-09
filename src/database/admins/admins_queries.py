"""Модуль для запросов к администраторам"""

from typing import List, Dict, Optional, Any
from ..base import get_db

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return c.fetchone() is not None

def is_super_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь суперадминистратором"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT is_super_admin FROM admins WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        return bool(result and result[0]) if result else False

def get_admin(user_id: int) -> Optional[Dict]:
    """Получение информации об администраторе"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        return dict(result) if result else None

def get_admin_info(user_id: int) -> Optional[Dict[str, Any]]:
    """Получение информации об администраторе (упрощенная версия)"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT user_id, username, first_name, added_by, added_at, is_super_admin
            FROM admins
            WHERE user_id = ?
        """, (user_id,))

        row = c.fetchone()
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'added_by': row[3],
                'added_at': row[4],
                'is_super_admin': bool(row[5])
            }

        return None

def get_all_admins() -> List[Dict]:
    """Получение всех администраторов"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM admins ORDER BY is_super_admin DESC, added_at")
        return [dict(row) for row in c.fetchall()]

def get_admins_count() -> int:
    """Получение количества администраторов"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM admins")
        return c.fetchone()[0]

def get_super_admins_count() -> int:
    """Получение количества суперадминистраторов"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM admins WHERE is_super_admin = TRUE")
        return c.fetchone()[0]

def get_admins_added_by(admin_id: int) -> List[Dict]:
    """Получение администраторов, добавленных конкретным администратором"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE added_by = ? ORDER BY added_at",
                  (admin_id,))
        return [dict(row) for row in c.fetchall()]
