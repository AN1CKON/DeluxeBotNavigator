# Конфигурация DeluxeBotNavigator
import os
import sys
import logging
from typing import Optional
from .logger_config import log_config_banner

# Получаем абсолютный путь к корню проекта
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Инициализация логгера для модуля конфигурации
logger = logging.getLogger(__name__)

def load_env_file():
    """Загружает переменные из .env файла если он существует"""
    env_file = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Загружаем .env файл если он существует
load_env_file()

# Основные настройки бота
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_STR = os.getenv("ADMIN_ID")

# Валидация обязательных параметров
if not TOKEN:
    print("❌ Ошибка: Не найден BOT_TOKEN!")
    print("Создайте файл .env или установите переменную окружения BOT_TOKEN")
    sys.exit(1)

if not ADMIN_ID_STR:
    print("❌ Ошибка: Не найден ADMIN_ID!")
    print("Создайте файл .env или установите переменную окружения ADMIN_ID")
    sys.exit(1)

try:
    ADMIN_ID = int(ADMIN_ID_STR)
except ValueError:
    print(f"❌ Ошибка: ADMIN_ID должен быть числом, получен: {ADMIN_ID_STR}")
    sys.exit(1)

# Пути к файлам (абсолютные от корня проекта)
DB_PATH = os.path.join(PROJECT_ROOT, "src", "database", "data", "menu.db")
MEDIA_PATH = os.path.join(PROJECT_ROOT, "src", "media")
IMG_PATH = os.path.join(PROJECT_ROOT, "src", "media", "image")
VIDEO_PATH = os.path.join(PROJECT_ROOT, "src", "media", "video")

# Настройки удаления сообщений
DEFAULT_DELETE_COUNT = 2
MAX_CLEAR_ATTEMPTS = 15
MAX_DELETE_RANGE = 1000

# Настройки уведомлений
CLEAR_NOTIFICATION_DELAY = 2.5
SUCCESS_NOTIFICATION_DELAY = 1.5

# Настройки безопасности
ADMIN_CHECK_REQUIRED = True

# Настройки email для отзывов
REVIEW_EMAIL = os.getenv("REVIEW_EMAIL")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def validate_config() -> bool:
    """Проверяет корректность конфигурации (дополнительные проверки)"""
    if not TOKEN or len(TOKEN) < 40:
        print("❌ Ошибка: TOKEN слишком короткий или пустой")
        return False
    if not TOKEN.count(':') == 1:
        print("❌ Ошибка: TOKEN имеет неверный формат (должен содержать ':')")
        return False
    if ADMIN_ID <= 0:
        print("❌ Ошибка: ADMIN_ID должен быть положительным числом")
        return False
    return True

def get_image_path(image_name: str) -> str:
    """Возвращает полный путь к изображению"""
    return os.path.join(IMG_PATH, image_name)

def get_video_path(video_name: str) -> str:
    """Возвращает полный путь к видео"""
    return os.path.join(VIDEO_PATH, video_name)

def print_config_info():
    """Выводит информацию о текущей конфигурации"""
    log_config_banner(TOKEN, ADMIN_ID, DB_PATH, IMG_PATH)
