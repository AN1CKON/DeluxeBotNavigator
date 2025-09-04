"""
DeluxeBot Navigator - Entry point
Точка входа для запуска бота
"""

import asyncio
import sys
import os

# Добавляем корневую папку в Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем и запускаем главную функцию
from src.bot.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)
