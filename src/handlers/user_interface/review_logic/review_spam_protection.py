"""Модуль защиты от спама для системы отзывов"""

import time
from typing import Optional, Tuple
from src.database.base import get_db

# Глобальный словарь для хранения ID сообщений по чатам
messages = {}


class SpamProtection:
    """Класс для защиты от спама в системе отзывов"""

    def __init__(self):
        self.cooldown_minutes = 0  # По умолчанию отключен (0 = без ограничений по времени)
        self.max_reviews_per_day = 3  # Максимум 3 отзыва в день
        self._load_settings()

    def _load_settings(self):
        """Загружает настройки из базы данных"""
        try:
            with get_db() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT cooldown_minutes, max_reviews_per_day
                    FROM review_spam_settings
                    WHERE id = 1
                """)
                result = c.fetchone()
                if result:
                    self.cooldown_minutes = result[0]
                    self.max_reviews_per_day = result[1]
        except Exception as e:
            # Если не удалось загрузить, используем значения по умолчанию
            print(f"⚠️ Не удалось загрузить настройки защиты от спама: {e}")

    def save_settings(self):
        """Сохраняет текущие настройки в базу данных"""
        try:
            with get_db() as conn:
                c = conn.cursor()
                c.execute("""
                    UPDATE review_spam_settings
                    SET cooldown_minutes = ?, max_reviews_per_day = ?, updated_at = datetime('now')
                    WHERE id = 1
                """, (self.cooldown_minutes, self.max_reviews_per_day))
                conn.commit()
        except Exception as e:
            print(f"⚠️ Не удалось сохранить настройки защиты от спама: {e}")

    def can_leave_review(self, user_id: int) -> Tuple[bool, str]:
        """
        Проверяет, может ли пользователь оставить отзыв

        Returns:
            Tuple[bool, str]: (можно ли оставить, сообщение об ошибке)
        """
        with get_db() as conn:
            c = conn.cursor()

            # Проверяем время последнего отзыва
            c.execute("""
                SELECT last_review_time, reviews_today, last_reset_date
                FROM user_review_limits
                WHERE user_id = ?
            """, (user_id,))

            result = c.fetchone()
            current_time = int(time.time())

            if result:
                last_review_time, reviews_today, last_reset_date = result

                # Проверяем, нужно ли сбросить счетчик отзывов (новый день)
                current_date = time.strftime("%Y-%m-%d")
                if last_reset_date != current_date:
                    reviews_today = 0
                    last_reset_date = current_date

                # Проверяем cooldown (если не отключен)
                if self.cooldown_minutes > 0:
                    time_diff = current_time - last_review_time
                    cooldown_seconds = self.cooldown_minutes * 60

                    if time_diff < cooldown_seconds:
                        remaining_minutes = (cooldown_seconds - time_diff) // 60
                        if remaining_minutes > 0:
                            return False, f"⏰ Подождите {remaining_minutes} мин. до следующего отзыва"
                        else:
                            return False, "⏰ Подождите еще немного до следующего отзыва"

                # Проверяем лимит на день
                if reviews_today >= self.max_reviews_per_day:
                    return False, f"📊 Достигнут дневной лимит отзывов ({self.max_reviews_per_day})"

                return True, ""

            else:
                # Первый отзыв пользователя
                return True, ""

    def record_review(self, user_id: int) -> None:
        """Записывает факт отправки отзыва"""
        with get_db() as conn:
            c = conn.cursor()
            current_time = int(time.time())
            current_date = time.strftime("%Y-%m-%d")

            # Проверяем, есть ли уже запись для пользователя
            c.execute("SELECT reviews_today, last_reset_date FROM user_review_limits WHERE user_id = ?", (user_id,))
            result = c.fetchone()

            if result:
                reviews_today, last_reset_date = result

                # Сбрасываем счетчик если новый день
                if last_reset_date != current_date:
                    reviews_today = 1
                else:
                    reviews_today += 1

                c.execute("""
                    UPDATE user_review_limits
                    SET last_review_time = ?, reviews_today = ?, last_reset_date = ?
                    WHERE user_id = ?
                """, (current_time, reviews_today, current_date, user_id))
            else:
                # Создаем новую запись
                c.execute("""
                    INSERT INTO user_review_limits (user_id, last_review_time, reviews_today, last_reset_date)
                    VALUES (?, ?, 1, ?)
                """, (user_id, current_time, current_date))

            conn.commit()

    def get_user_stats(self, user_id: int) -> dict:
        """Получает статистику пользователя по отзывам"""
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT last_review_time, reviews_today, last_reset_date
                FROM user_review_limits
                WHERE user_id = ?
            """, (user_id,))

            result = c.fetchone()
            if result:
                last_review_time, reviews_today, last_reset_date = result
                current_time = int(time.time())

                return {
                    'last_review_time': last_review_time,
                    'reviews_today': reviews_today,
                    'time_since_last_review': current_time - last_review_time,
                    'cooldown_remaining': max(0, (self.cooldown_minutes * 60) - (current_time - last_review_time))
                }

            return {
                'last_review_time': None,
                'reviews_today': 0,
                'time_since_last_review': 0,
                'cooldown_remaining': 0
            }


# Глобальный экземпляр защиты от спама
spam_protection = SpamProtection()
