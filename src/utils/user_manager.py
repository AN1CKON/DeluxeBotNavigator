#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилита для тестирования и управления системой пользователей DeluxeBot
"""

import sqlite3
import sys
import os
from pathlib import Path
from src.config.config import DB_PATH

# Добавляем корневую папку проекта в Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def show_users():
    """Показывает всех пользователей в базе данных"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, username, first_name, welcome_shown, first_visit, last_visit 
            FROM users ORDER BY first_visit DESC
        """)
        
        users = cursor.fetchall()
        
        print("👥 ПОЛЬЗОВАТЕЛИ В БАЗЕ ДАННЫХ:")
        print("-" * 80)
        
        if not users:
            print("📭 Пользователей пока нет")
        else:
            for user in users:
                user_id, username, first_name, welcome_shown, first_visit, last_visit = user
                
                status = "✅ Прошел приветствие" if welcome_shown else "🔥 Новый пользователь"
                name = first_name or "Без имени"
                username_str = f"@{username}" if username else "Без username"
                
                print(f"👤 {name} ({username_str})")
                print(f"   ID: {user_id}")
                print(f"   Статус: {status}")
                print(f"   Первый визит: {first_visit}")
                print(f"   Последний визит: {last_visit}")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def reset_user_welcome(user_id):
    """Сбрасывает статус приветствия для пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET welcome_shown = FALSE WHERE user_id = ?", (user_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Статус приветствия сброшен для пользователя {user_id}")
        else:
            print(f"❌ Пользователь {user_id} не найден")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def delete_user(user_id):
    """Удаляет пользователя из базы данных"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Пользователь {user_id} удален из базы данных")
        else:
            print(f"❌ Пользователь {user_id} не найден")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Основная функция с меню"""
    while True:
        print("\n🔧 УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ DELUXEBOT")
        print("1. 👥 Показать всех пользователей")
        print("2. 🔄 Сбросить приветствие для пользователя")
        print("3. 🗑️ Удалить пользователя")
        print("4. 🚪 Выход")
        
        choice = input("\nВыберите действие (1-4): ").strip()
        
        if choice == "1":
            show_users()
            
        elif choice == "2":
            user_id = input("Введите ID пользователя: ").strip()
            try:
                reset_user_welcome(int(user_id))
            except ValueError:
                print("❌ Некорректный ID пользователя")
                
        elif choice == "3":
            user_id = input("Введите ID пользователя для удаления: ").strip()
            try:
                delete_user(int(user_id))
            except ValueError:
                print("❌ Некорректный ID пользователя")
                
        elif choice == "4":
            print("👋 До свидания!")
            break
            
        else:
            print("❌ Некорректный выбор")

if __name__ == "__main__":
    main()
