"""Обработчик формы отзыва"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from ..common.utils import safe_delete_message
from ...models.states import ReviewStates
from ...utils.texts import *
from ...config.config import REVIEW_EMAIL, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD

async def show_review_form(message: types.Message, state: FSMContext):
    """Показывает форму для написания отзыва"""
    await safe_delete_message(message)

    # Создаем клавиатуру для формы отзыва
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="cancel_review")]
    ])

    await message.answer(MSG_REVIEW_FORM, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(ReviewStates.waiting_for_review_content)

async def send_review_email(review_text: str, user_info: dict) -> bool:
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
        msg['Subject'] = f"Отзыв от пользователя {user_info.get('username', 'Unknown')}"

        # Текст сообщения
        body = f"""
Новый отзыв от пользователя:

👤 Пользователь: @{user_info.get('username', 'Не указан')}
🆔 ID: {user_info.get('id', 'Не указан')}
📝 Имя: {user_info.get('first_name', 'Не указано')} {user_info.get('last_name', '')}

💬 Отзыв:
{review_text}

---
Отправлено из Telegram бота DeluxeBotNavigator
        """.strip()

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Отправляем email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, REVIEW_EMAIL, text)
        server.quit()

        return True

    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")
        return False

def register_review_handlers(dp):
    """Регистрация обработчиков формы отзыва"""

    @dp.message(ReviewStates.waiting_for_review_content)
    async def handle_review_content(message: types.Message, state: FSMContext):
        """Обработка текста отзыва"""
        review_text = message.text.strip()

        # Проверяем длину отзыва
        if len(review_text) < 10:
            await message.answer(
                MSG_REVIEW_TOO_SHORT.format(length=len(review_text)),
                parse_mode="HTML"
            )
            return

        # Получаем информацию о пользователе
        user_info = {
            'id': message.from_user.id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name
        }

        # Отправляем отзыв на email
        success = await send_review_email(review_text, user_info)

        if success:
            await message.answer(MSG_REVIEW_SUCCESS, parse_mode="HTML")
        else:
            await message.answer(MSG_REVIEW_ERROR, parse_mode="HTML")

        # Очищаем состояние
        await state.clear()

    @dp.callback_query(F.data == "cancel_review")
    async def cancel_review(callback: types.CallbackQuery, state: FSMContext):
        """Отмена формы отзыва"""
        await safe_delete_message(callback.message)
        await callback.message.answer("❌ Отзыв отменен")
        await state.clear()
