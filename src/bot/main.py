"""
DeluxeBotNavigator - Telegram Menu Bot
Простой и элегантный бот для создания навигационных меню в Telegram
"""

import asyncio
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.config.config import TOKEN, validate_config, print_config_info
from src.database.db import init_db
from src.handlers import register_handlers
from src.config.logger_config import setup_logging, get_logger, log_startup_banner, log_shutdown_banner, log_project_stats

# Настройка красивого логирования
setup_logging(console_level="INFO", file_level="DEBUG")
logger = get_logger(__name__)

async def main():
    """Главная функция запуска бота"""
    try:
        # Красивый баннер запуска
        log_startup_banner()
        
        # Дополнительная проверка конфигурации
        logger.info("🔍 Проверка конфигурации...")
        if not validate_config():
            logger.error("❌ Ошибка валидации конфигурации!")
            return
        
        # Показываем информацию о конфигурации
        print_config_info()
        
        # Инициализация базы данных
        logger.info("🗄️ Инициализация базы данных...")
        init_db()
        logger.info("✅ База данных инициализирована")
        
        # Создание бота и диспетчера
        logger.info("🤖 Создание экземпляра бота...")
        bot = Bot(token=TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрация обработчиков
        logger.info("📝 Регистрация обработчиков...")
        register_handlers(dp, bot)
        logger.info("✅ Обработчики зарегистрированы")
        
        # Показываем статистику проекта
        logger.info("📊 Статистика проекта:")
        log_project_stats()
        
        # Запуск polling
        logger.info("🚀 Запуск polling...")
        logger.info("🎯 DeluxeBotNavigator готов к работе!")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при запуске: {e}", exc_info=True)
    finally:
        try:
            await bot.session.close()
            logger.info("🔌 Соединение с Telegram API закрыто")
        except:
            pass
        log_shutdown_banner()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
