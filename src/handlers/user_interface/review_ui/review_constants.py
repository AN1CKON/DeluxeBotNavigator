"""Константы для системы отзывов"""

# Состояния FSM
REVIEW_STATES = {
    'WAITING_FOR_RATING': 'waiting_for_rating',
    'WAITING_FOR_REVIEW_CONTENT': 'waiting_for_review_content'
}

# Описания оценок
RATING_DESCRIPTIONS = {
    1: "1⭐ Тильт",
    2: "2⭐ Кринж",
    3: "3⭐ Нормис",
    4: "4⭐ Свага",
    5: "5⭐ Полный фарш!"
}

# Минимальная и максимальная длина отзыва
REVIEW_MIN_LENGTH = 15
REVIEW_MAX_LENGTH = 300

# Таймер для сообщения успеха (секунды)
SUCCESS_MESSAGE_DURATION = 10
