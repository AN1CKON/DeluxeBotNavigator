"""
Красивая система логирования для DeluxeBotNavigator
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для консольного вывода"""
    
    # ANSI цветовые коды
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
        'BOLD': '\033[1m',        # Bold
        'DIM': '\033[2m',         # Dim
    }
    
    # Эмодзи для уровней логирования
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '✅', 
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
    }
    
    def format(self, record):
        # Получаем цвет и эмодзи для уровня
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        emoji = self.EMOJIS.get(record.levelname, '📝')
        reset = self.COLORS['RESET']
        bold = self.COLORS['BOLD']
        dim = self.COLORS['DIM']
        
        # Форматируем время
        time_str = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Сокращаем имя логгера для читаемости
        logger_name = record.name.split('.')[-1] if '.' in record.name else record.name
        if logger_name == '__main__':
            logger_name = 'Main'
        
        # Формируем красивое сообщение
        formatted = (
            f"{dim}{time_str}{reset} "
            f"{emoji} "
            f"{color}{bold}{record.levelname:<8}{reset} "
            f"{dim}[{logger_name}]{reset} "
            f"{record.getMessage()}"
        )
        
        # Добавляем информацию об исключении если есть
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
            
        return formatted

class FileFormatter(logging.Formatter):
    """Простой форматтер для файлового вывода"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

def setup_logging(
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Настраивает красивую систему логирования
    
    Args:
        console_level: Уровень логирования для консоли
        file_level: Уровень логирования для файла  
        log_file: Путь к файлу логов (если None, то logs/deluxebot.log)
        max_file_size: Максимальный размер файла лога
        backup_count: Количество файлов для ротации
    """
    
    # Создаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Очищаем существующие обработчики
    root_logger.handlers.clear()
    
    # === КОНСОЛЬНЫЙ ОБРАБОТЧИК ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)
    
    # === ФАЙЛОВЫЙ ОБРАБОТЧИК ===
    if log_file is None:
        # Создаем папку для логов
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / f"deluxebot_{datetime.now().strftime('%Y%m%d')}.log"
    
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(FileFormatter())
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Если не удается создать файловый обработчик, продолжаем только с консольным
        console_handler.handle(logging.makeLogRecord({
            'name': 'Logging',
            'level': logging.WARNING,
            'pathname': __file__,
            'lineno': 0,
            'msg': f"Не удалось создать файловый обработчик: {e}",
            'args': (),
            'exc_info': None
        }))
    
    # Настраиваем логирование для aiogram (уменьшаем детализацию)
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Получить логгер с заданным именем"""
    return logging.getLogger(name)

def log_startup_banner():
    """Выводит красивый баннер запуска"""
    logger = get_logger(__name__)
    
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 DeluxeBotNavigator                     
║            Элегантный Telegram бот для навигации              
╚══════════════════════════════════════════════════════════════╝
    """
    
    # Выводим баннер линия за линией
    for line in banner.strip().split('\n'):
        print(f"\033[36m{line}\033[0m")  # Cyan цвет
    
    logger.info("🚀 Запуск DeluxeBotNavigator...")

def log_shutdown_banner():
    """Выводит баннер завершения работы"""
    logger = get_logger(__name__)
    
    logger.info("👋 DeluxeBotNavigator завершает работу...")
    print(f"\033[36m{'═' * 62}\033[0m")
    print(f"\033[36m✨ Спасибо за использование DeluxeBotNavigator! ✨\033[0m")
    print(f"\033[36m{'═' * 62}\033[0m")

def log_config_banner(token: str, admin_id: int, db_path: str, img_path: str):
    """Выводит красивый баннер конфигурации"""
    
    # Маскируем токен
    masked_token = f"{token[:10]}...{token[-10:]}"
    
    # Форматируем каждую строку с точным количеством символов
    lines = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║                    ⚙️  Конфигурация системы                   ",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║ 📋 Токен бота:         {masked_token:<30}",
        f"║ 👤 ID Администратора:  {str(admin_id):<30} ",
        f"║ 🗄️  База данных:        {db_path:<30}",
        f"║ 🖼️  Папка изображений:  {img_path:<29}",
        "╚══════════════════════════════════════════════════════════════╝"
    ]
    
    # Выводим баннер линия за линией
    for line in lines:
        print(f"\033[32m{line}\033[0m")  # Green цвет

def log_project_stats():
    """Выводит красивую статистику проекта"""
    
    import os
    from pathlib import Path
    
    # Подсчитываем статистику
    python_files = 0
    total_lines = 0
    code_lines = 0
    handlers_count = 0
    functions_count = 0
    
    # Сканируем Python файлы
    for root, dirs, files in os.walk('.'):
        # Пропускаем .venv и __pycache__
        dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__']]
        
        for file in files:
            if file.endswith('.py'):
                python_files += 1
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.readlines()
                        total_lines += len(content)
                        code_lines += len([line for line in content if line.strip()])
                        
                        # Подсчитываем обработчики и функции
                        file_content = ''.join(content)
                        handlers_count += file_content.count('@dp.message') + file_content.count('@dp.callback_query')
                        functions_count += file_content.count('def ')
                except:
                    pass
    
    # Подсчитываем другие файлы
    images_count = len(list(Path('img').glob('*'))) if Path('img').exists() else 0
    config_files = len([f for f in os.listdir('.') if f.endswith(('.md', '.txt', '.env'))])
    
    # Процент полезного кода
    code_percentage = round((code_lines / total_lines * 100), 1) if total_lines > 0 else 0
    
    # Форматируем статистику
    lines = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║                    📊 Статистика проекта                     ",
        "║                       DeluxeBotNavigator                      ",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║ 🐍 Python файлов:     {str(python_files):<30}    ",
        f"║ 📝 Всего строк:       {str(total_lines):<30}    ", 
        f"║ 💻 Строк с кодом:     {str(code_lines):<30}    ",
        f"║ ⚡ Обработчиков:      {str(handlers_count):<30}    ",
        f"║ 🔧 Функций:           {str(functions_count):<30}    ",
        f"║ 🖼️  Изображений:       {str(images_count):<30}    ",
        f"║ 📄 Конфиг. файлов:    {str(config_files):<30}    ",
        f"║ 📈 Полезный код:      {str(code_percentage)}%{'':<27}    ",
        "╚══════════════════════════════════════════════════════════════╝"
    ]
    
    # Выводим статистику
    for line in lines:
        print(f"\033[35m{line}\033[0m")  # Magenta цвет
