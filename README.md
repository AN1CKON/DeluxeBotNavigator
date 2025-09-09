<div align="center">

# 🤖 DeluxeBot Navigator

**Профессиональный Telegram бот для создания интерактивных навигационных меню**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.4.1-green.svg)](https://aiogram.dev)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

---

*Создавайте красивые интерактивные меню для Telegram с мощной админ-панелью*

[⚡ Быстрый старт](#-быстрый-старт) • [📚 Документация](docs/project/DOCUMENTATION.md) • [⚙️ Настройка](docs/project/CONFIG_GUIDE.md)

</div>

## ✨ Что умеет бот

### 🎯 Основные возможности
- **Интерактивные меню** - Создание многоуровневых навигационных структур
- **Медиа поддержка** - Изображения, видео и кнопки с картинками
- **Админ-панель** - Полное управление через удобный интерфейс
- **Гибкая настройка** - Различные типы контента (текст, ссылки, подменю)

### 🛠️ Управление меню
- ➕ **Добавление** новых пунктов и разделов
- ✏️ **Редактирование** существующих элементов
- 🗑️ **Удаление** пунктов и целых разделов
- 📦 **Перемещение** элементов между уровнями
- 🗂️ **Организация** в иерархические структуры

## 🚀 Быстрый старт

### 📋 Требования
- **Python 3.8+** (рекомендуется Python 3.10+)
- **Telegram Bot Token** ([получить у @BotFather](https://t.me/BotFather))
- **Интернет-соединение** для работы с Telegram API

### ⚡ Установка (3 шага)

1. **Клонируйте и установите:**
   ```bash
   git clone https://github.com/AN1CKON/DeluxeBotNavigator.git
   cd DeluxeBotNavigator
   pip install -r docs/project/requirements.txt
   ```

2. **Настройте переменные:**
   ```bash
   copy .env.example .env  # Windows
   # cp .env.example .env    # Linux/Mac
   ```

   Отредактируйте `.env`:
   ```env
   BOT_TOKEN=ваш_токен_бота
   ADMIN_ID=ваш_telegram_id
   ```

3. **Запустите бота:**
   ```bash
   python run.py
   ```

🎉 **Готово!** Бот запущен и готов к работе.

## 📖 Как использовать

### 👤 Для пользователей
1. Найдите бота в Telegram
2. Отправьте `/start`
3. Используйте интерактивное меню

### 👨‍💼 Для администраторов
1. Убедитесь, что ваш ID указан в `ADMIN_ID`
2. Отправьте `/admin` для входа в панель управления
3. Создавайте и настраивайте меню через интерфейс

## 📁 Структура проекта

```
DeluxeBotNavigator/
├── run.py                # 🚀 Точка входа
├── .env.example          # ⚙️ Шаблон конфигурации
├── docs/                 # 📚 Документация
├── client_docs/          # 📋 Документы для клиентов
├── logs/                 # 📝 Логи работы
└── src/                  # 💻 Исходный код
    ├── bot/              # 🤖 Основная логика
    ├── config/           # ⚙️ Конфигурация
    ├── database/         # �️ База данных
    ├── handlers/         # 🎛️ Обработчики
    ├── keyboards/        # ⌨️ Клавиатуры
    ├── media/            # 🎨 Медиа файлы
    ├── models/           # 📊 Модели данных
    └── utils/            # � Утилиты
```

## 🔧 Технологии

- **Python 3.8+** - Основной язык
- **Aiogram 3.4.1** - Фреймворк для Telegram ботов
- **SQLite** - База данных
- **Aiofiles** - Работа с файлами

## 📄 Лицензия

[Commercial License](LICENSE) - Коммерческая лицензия для [IDELUXE COURSE].

Для приобретения лицензии или получения поддержки свяжитесь с разработчиком.

---

<div align="center">

**⭐ Поставьте звездочку, если проект понравился!**

[GitHub](https://github.com/AN1CKON) • [Telegram](https://t.me/yourusername) • [Email](mailto:ai.kakoyto.steam@gmail.com)

</div>
