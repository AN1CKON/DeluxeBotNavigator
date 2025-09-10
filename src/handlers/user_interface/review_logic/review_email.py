"""Модуль для отправки email отзывов"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.handlers.user_interface.review_ui.review_constants import RATING_DESCRIPTIONS
from src.config.config import REVIEW_EMAIL, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD


def send_review_email(review_text: str, rating: int, user_info: dict) -> bool:
    """Отправляет отзыв на email"""
    try:
        # Проверяем конфигурацию email
        if not all([REVIEW_EMAIL, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
            print("❌ Конфигурация email не настроена")
            return False

        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = REVIEW_EMAIL
        msg['Subject'] = f"Отзыв от пользователя {user_info.get('username', 'Unknown')} - Оценка: {rating}/5"

        # Текст сообщения
        rating_text = RATING_DESCRIPTIONS.get(rating, f"⭐{'⭐' * (rating - 1)}")
        body = f"""
Новый отзыв от пользователя:

👤 Пользователь: @{user_info.get('username', 'Не указан')}
🆔 ID: {user_info.get('id', 'Не указан')}
📝 Имя: {user_info.get('first_name', 'Не указано')} {user_info.get('last_name', '')}
⭐ Оценка: {rating_text} ({rating}/5)

💬 Отзыв:
{review_text}

---
Отправлено из Telegram бота DeluxeBotNavigator
        """.strip()

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Отправляем email
        if SMTP_PORT == 465:
            # SSL соединение
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        else:
            # STARTTLS соединение (для портов 587, 25)
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)

        server.sendmail(SMTP_USERNAME, REVIEW_EMAIL, msg.as_string())
        server.quit()

        return True

    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")
        return False
