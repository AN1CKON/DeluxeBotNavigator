"""Модуль для получения статистики по администраторам"""

from typing import Dict
from ..base import get_db

def get_admins_statistics() -> Dict[str, int]:
    """Получение статистики по администраторам"""
    with get_db() as conn:
        c = conn.cursor()

        stats = {}

        # Общее количество администраторов
        c.execute("SELECT COUNT(*) FROM admins")
        stats['total_admins'] = c.fetchone()[0]

        # Количество суперадминистраторов
        c.execute("SELECT COUNT(*) FROM admins WHERE is_super_admin = TRUE")
        stats['super_admins'] = c.fetchone()[0]

        # Количество обычных администраторов
        stats['regular_admins'] = stats['total_admins'] - stats['super_admins']

        # Новые администраторы (последние 30 дней)
        c.execute('''SELECT COUNT(*) FROM admins
                     WHERE added_at > datetime('now', '-30 days')''')
        stats['new_admins_30d'] = c.fetchone()[0]

        return stats
