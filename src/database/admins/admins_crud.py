"""Модуль для CRUD операций с администраторами"""

import logging
from typing import Optional
from ..base import get_db

logger = logging.getLogger(__name__)

def add_admin(user_id: int, username: Optional[str] = None,
              first_name: Optional[str] = None, added_by: Optional[int] = None,
              is_super_admin: bool = False) -> bool:
    """Добавление администратора"""
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO admins
                         (user_id, username, first_name, added_by, is_super_admin)
                         VALUES (?, ?, ?, ?, ?)''',
                      (user_id, username, first_name, added_by, is_super_admin))
            conn.commit()
            admin_type = "суперадминистратор" if is_super_admin else "администратор"
            logger.info(f"👑 Добавлен {admin_type}: {username or first_name or user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления администратора {user_id}: {e}")
            return False

def remove_admin(user_id: int) -> bool:
    """Удаление администратора"""
    with get_db() as conn:
        c = conn.cursor()

        # Получаем информацию об администраторе перед удалением
        c.execute("SELECT username, first_name FROM admins WHERE user_id = ?", (user_id,))
        admin_info = c.fetchone()

        if not admin_info:
            logger.warning(f"⚠️ Администратор с ID {user_id} не найден")
            return False

        c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        deleted = c.rowcount > 0

        if deleted:
            conn.commit()
            admin_name = admin_info[0] or admin_info[1] or str(user_id)
            logger.info(f"🗑️ Удален администратор: {admin_name}")

        return deleted

def update_admin_info(user_id: int, username: Optional[str] = None,
                     first_name: Optional[str] = None) -> bool:
    """Обновление информации об администраторе"""
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
        query = f"UPDATE admins SET {', '.join(updates)} WHERE user_id = ?"
        c.execute(query, params)
        updated = c.rowcount > 0
        if updated:
            conn.commit()
            logger.info(f"📝 Обновлена информация администратора ID: {user_id}")
        return updated

def clear_all_admins() -> None:
    """Удаление всех администраторов (ОСТОРОЖНО!)"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM admins")
        conn.commit()
        logger.warning("⚠️ Все администраторы удалены!")
