"""Модуль для работы со статистикой плагинов"""

import logging
from typing import List, Dict, Optional
from .base import get_db

logger = logging.getLogger(__name__)

def add_plugin_stat(name: str, status: str, progress: int = 0) -> bool:
    """Добавляет новую запись статистики плагина"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO plugin_stats (name, status, progress)
                VALUES (?, ?, ?)
            """, (name, status, progress))
            conn.commit()
            logger.info(f"✅ Добавлена статистика для плагина: {name}")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка добавления статистики плагина: {e}")
        return False

def update_plugin_stat(plugin_id: int, name: str = None, status: str = None, progress: int = None) -> bool:
    """Обновляет запись статистики плагина"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if progress is not None:
                updates.append("progress = ?")
                params.append(progress)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(plugin_id)
                
                c.execute(f"""
                    UPDATE plugin_stats 
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                conn.commit()
                logger.info(f"✅ Обновлена статистика плагина ID: {plugin_id}")
                return True
    except Exception as e:
        logger.error(f"❌ Ошибка обновления статистики плагина: {e}")
        return False

def delete_plugin_stat(plugin_id: int) -> bool:
    """Удаляет запись статистики плагина"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM plugin_stats WHERE id = ?", (plugin_id,))
            conn.commit()
            logger.info(f"✅ Удалена статистика плагина ID: {plugin_id}")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка удаления статистики плагина: {e}")
        return False

def get_all_plugin_stats() -> List[Dict]:
    """Получает все записи статистики плагинов"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, name, status, progress, created_at, updated_at
                FROM plugin_stats
                ORDER BY name
            """)
            rows = c.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики плагинов: {e}")
        return []

def get_plugin_stat_by_id(plugin_id: int) -> Optional[Dict]:
    """Получает запись статистики плагина по ID"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, name, status, progress, created_at, updated_at
                FROM plugin_stats
                WHERE id = ?
            """, (plugin_id,))
            row = c.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики плагина: {e}")
        return None

def format_plugin_stats_message() -> str:
    """Форматирует сообщение со статистикой плагинов"""
    stats = get_all_plugin_stats()
    
    if not stats:
        return "📊 Статистика плагинов:\n\nℹ️ Нет данных о плагинах"
    
    message = "📊 Статистика обновлений плагинов:\n\n"
    
    for stat in stats:
        name = stat['name']
        status = stat['status']
        progress = stat['progress']
        
        if status == 'актуален':
            message += f"✅ {name}\n└─➤ Актуален\n\n"
        else:
            message += f"🔄 {name}\n└─➤ На обновлении ({progress}%)\n\n"
    
    return message
