# ИНСТРУКЦИЯ ПО УСТАНОВКЕ
# DeluxeBot Navigator

## 📋 Системные требования

- **Операционная система**: Windows 10+, Linux (Ubuntu 18.04+), macOS 10.15+
- **Python**: версия 3.8 или выше
- **ОЗУ**: минимум 512 MB
- **Место на диске**: 100 MB
- **Интернет-соединение**: для работы с Telegram API

## ⚡ Быстрая установка

### Шаг 1: Установка Python
Если Python не установлен, скачайте с официального сайта:
https://python.org/downloads/

### Шаг 2: Клонирование проекта
```bash
git clone [ссылка на ваш репозиторий]
cd DeluxeBotNavigator
```

### Шаг 3: Установка зависимостей
```bash
pip install -r docs/project/requirements.txt
```

### Шаг 4: Настройка переменных окружения
Создайте файл `.env` в корневой папке проекта:

```env
# Токен вашего Telegram бота
BOT_TOKEN=ваш_токен_бота

# Ваш Telegram ID (для администратора)
ADMIN_ID=ваш_telegram_id

# Другие настройки (если нужны)
```

### Шаг 5: Запуск бота
```bash
python run.py
```

## 🔧 Настройка сервера (рекомендуется)

### Использование Docker
```bash
# Создать образ
docker build -t deluxebot .

# Запустить контейнер
docker run -d --name deluxebot deluxebot
```

### Использование systemd (Linux)
Создайте файл `/etc/systemd/system/deluxebot.service`:

```ini
[Unit]
Description=DeluxeBot Navigator
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/DeluxeBotNavigator
ExecStart=/usr/bin/python3 run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Включить и запустить сервис
sudo systemctl enable deluxebot
sudo systemctl start deluxebot
```

## 📱 Настройка Telegram бота

### Получение токена бота
1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте токен и вставьте в `.env`

### Получение вашего Telegram ID
1. Напишите [@userinfobot](https://t.me/userinfobot)
2. Отправьте любое сообщение
3. Скопируйте ваш ID и вставьте в `.env`

## 🔍 Проверка установки

После запуска бота:
1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Отправьте `/admin` (только для администратора)
4. Проверьте работу основных функций

## 🆘 Устранение проблем

### Бот не отвечает
- Проверьте токен бота
- Убедитесь, что бот запущен
- Проверьте логи в папке `logs/`

### Ошибка подключения
- Проверьте интернет-соединение
- Убедитесь, что все зависимости установлены
- Проверьте настройки firewall

### Проблемы с базой данных
- Убедитесь, что папка `src/database/data/` доступна для записи
- Проверьте права доступа к файлам

## 📞 Техническая поддержка

При возникновении проблем:
- Email: [ваш email]
- Telegram: [ваш telegram]
- Время ответа: в течение 24 часов

## 📋 Дополнительная информация

- **Документация**: см. `docs/project/DOCUMENTATION.md`
- **Логи**: хранятся в папке `logs/`
- **База данных**: `src/database/data/menu.db`
- **Медиа файлы**: хранятся в `src/media/`
