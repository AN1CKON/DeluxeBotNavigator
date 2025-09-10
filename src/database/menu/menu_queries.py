"""Модуль для запросов к элементам меню"""

import sqlite3
from typing import List, Dict, Optional, Tuple
from src.database.base import get_db

def get_menu_item_by_id(item_id: int) -> Optional[Dict]:
    """Получение элемента меню по ID"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM menu WHERE id = ?", (item_id,))
        result = c.fetchone()
        return dict(result) if result else None

def get_menu_item(item_id: int) -> Optional[sqlite3.Row]:
    """Получает конкретный пункт меню по ID (возвращает Row объект)"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM menu WHERE id = ?", (item_id,))
        return c.fetchone()

def get_all_menu_items() -> List[Dict]:
    """Получение всех элементов меню"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM menu ORDER BY parent_id, position")
        return [dict(row) for row in c.fetchall()]

def get_child_menu_items(parent_id: Optional[int]) -> List[Dict]:
    """Получение дочерних элементов меню"""
    with get_db() as conn:
        c = conn.cursor()
        query = "SELECT * FROM menu WHERE parent_id " + \
                ("IS NULL" if parent_id is None else "= ?") + \
                " ORDER BY position"
        params = () if parent_id is None else (parent_id,)
        c.execute(query, params)
        return [dict(row) for row in c.fetchall()]

def get_menu_items(parent_id: Optional[int] = None) -> List[Tuple[int, str]]:
    """Получает список пунктов меню, отсортированных по позиции"""
    with get_db() as conn:
        c = conn.cursor()
        query = "SELECT id, title FROM menu WHERE parent_id " + \
                ("IS NULL" if parent_id is None else "= ?") + " ORDER BY position ASC"
        params = () if parent_id is None else (parent_id,)
        c.execute(query, params)
        return c.fetchall()

def get_menu_items_with_positions(parent_id: Optional[int] = None) -> List[Tuple[int, str, int]]:
    """Получает список пунктов меню с их позициями"""
    with get_db() as conn:
        c = conn.cursor()
        query = "SELECT id, title, position FROM menu WHERE parent_id " + \
                ("IS NULL" if parent_id is None else "= ?") + " ORDER BY position ASC"
        params = () if parent_id is None else (parent_id,)
        c.execute(query, params)
        return c.fetchall()

def get_menu_items_grouped(parent_id: Optional[int] = None) -> List[List[Tuple[int, str, int]]]:
    """Получает элементы меню, группированные по позициям для отображения в клавиатуре (новый алгоритм)"""
    with get_db() as conn:
        c = conn.cursor()
        query = "SELECT id, title, position FROM menu WHERE parent_id " + \
                ("IS NULL" if parent_id is None else "= ?") + " ORDER BY position ASC, id ASC"
        params = () if parent_id is None else (parent_id,)
        c.execute(query, params)

        items = c.fetchall()
        if not items:
            return []

        # Группируем по позициям
        grouped = []
        current_group = []
        current_position = None

        for item in items:
            item_id, title, position = item

            if current_position is None or position != current_position:
                # Начинаем новую группу
                if current_group:
                    grouped.append(current_group)
                current_group = [(item_id, title, position)]
                current_position = position
            else:
                # Добавляем к текущей группе
                current_group.append((item_id, title, position))

        # Добавляем последнюю группу
        if current_group:
            grouped.append(current_group)

        return grouped
