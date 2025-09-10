"""Обработчик формы отзыва"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from ..common.utils import safe_delete_message
from ...models.states import ReviewStates
from ...utils.texts import *
from ...config.config import REVIEW_EMAIL, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD

# Глобальная переменная для отслеживания ID сообщения успеха
current_success_message_id = None

# Глобальная переменная для предотвращения повторного открытия формы отзыва
review_recently_completed = False
from ..common.utils import safe_delete_message
from ...models.states import ReviewStates
from ...utils.texts import *
from ...config.config import REVIEW_EMAIL, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD

async def show_review_form(message: types.Message, state: FSMContext):
    """Показывает форму для написания отзыва"""
    # Проверяем, не был ли отзыв только что успешно отправлен
    global review_recently_completed
    if review_recently_completed:
        # Сбрасываем флаг и не показываем форму повторно
        review_recently_completed = False
        return

    # Не удаляем главное меню - показываем форму как новое сообщение

    # Создаем интерактивную клавиатуру для выбора оценки
    keyboard = await create_rating_keyboard(0)  # 0 означает, что ничего не выбрано

    # Отправляем сообщение с формой отзыва и сохраняем его ID
    review_form_message = await message.answer(MSG_REVIEW_RATING, reply_markup=keyboard, parse_mode="HTML")
    await state.update_data(review_form_message_id=review_form_message.message_id)
    await state.set_state(ReviewStates.waiting_for_rating)

async def create_rating_keyboard(selected_rating: int) -> types.InlineKeyboardMarkup:
    """Создает интерактивную клавиатуру для выбора оценки"""
    stars = []

    # Создаем ряд звездочек (от 1 до 5)
    star_row = []
    for i in range(1, 6):  # От 1 до 5
        if i <= selected_rating:
            # Выбранные звезды - золотые
            star_text = f"⭐"
        else:
            # Невыбранные звезды - серые
            star_text = f"☆"

        star_row.append(
            types.InlineKeyboardButton(
                text=star_text,
                callback_data=f"star_{i}"
            )
        )

    stars.append(star_row)

    # Добавляем кнопки управления
    control_row = []

    # Сначала добавляем кнопку "Закрыть"
    control_row.append(
        types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close_review"
        )
    )

    # Потом добавляем кнопку "Подтвердить" (если оценка выбрана)
    if selected_rating > 0:
        control_row.append(
            types.InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data="confirm_rating"
            )
        )

    stars.append(control_row)

    return types.InlineKeyboardMarkup(inline_keyboard=stars)

async def send_review_email(review_text: str, rating: int, user_info: dict) -> bool:
    """Отправляет отзыв на email"""
    try:
        # Проверяем конфигурацию email
        if not all([REVIEW_EMAIL, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
            print("❌ Конфигурация email не настроена")
            return False

        # Преобразуем оценку в текстовое описание
        rating_descriptions = {
            1: "1⭐ Тильт",
            2: "2⭐ Кринж",
            3: "3⭐ Нормис",
            4: "4⭐ Свага",
            5: "5⭐ Полный фарш!"
        }
        rating_text = rating_descriptions.get(rating, f"⭐{'⭐' * (rating - 1)}")

        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = REVIEW_EMAIL
        msg['Subject'] = f"Отзыв от пользователя {user_info.get('username', 'Unknown')} - Оценка: {rating}/5"

        # Текст сообщения
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

        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, REVIEW_EMAIL, text)
        server.quit()

        return True

    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")
        return False

async def show_success_with_timer(message: types.Message, duration: int = 10):
    """Показывает сообщение успеха с таймером обратного отсчета"""
    print(f"DEBUG: Начинаем таймер на {duration} секунд")
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=BUTTON_OK, callback_data="close_success")]
    ])

    success_message = await message.answer(
        MSG_REVIEW_SUCCESS_WITH_TIMER.format(seconds=duration),
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    print(f"DEBUG: Сообщение успеха отправлено, ID: {success_message.message_id}")

    # Сохраняем ID сообщения в глобальной переменной для проверки в обработчике
    global current_success_message_id
    current_success_message_id = success_message.message_id

    # Запоминаем предыдущий текст для проверки изменений
    previous_text = MSG_REVIEW_SUCCESS_WITH_TIMER.format(seconds=duration)

    # Запускаем таймер обратного отсчета
    for remaining in range(duration, 0, -1):
        print(f"DEBUG: Таймер: {remaining} секунд осталось")
        await asyncio.sleep(1)  # Ждем 1 секунду

        # Проверяем, не было ли сообщение удалено пользователем (current_success_message_id станет None)
        if current_success_message_id is None:
            print("DEBUG: Сообщение было удалено пользователем")
            break

        # Создаем новый текст
        new_text = MSG_REVIEW_SUCCESS_WITH_TIMER.format(seconds=remaining)
        
        # Проверяем, изменился ли текст
        if new_text != previous_text:
            try:
                await success_message.edit_text(
                    new_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                print(f"DEBUG: Сообщение обновлено: {remaining} секунд")
                previous_text = new_text
            except Exception as e:
                error_message = str(e)
                if "message is not modified" in error_message:
                    print(f"DEBUG: Сообщение не изменилось, пропускаем обновление")
                else:
                    print(f"DEBUG: Ошибка при обновлении сообщения: {error_message}")
                    # Сообщение могло быть удалено
                    break
        else:
            print(f"DEBUG: Текст не изменился, пропускаем обновление")

    # После завершения таймера удаляем сообщение (если оно еще не удалено)
    if current_success_message_id is not None:
        print("DEBUG: Удаляем сообщение после завершения таймера")
        try:
            await success_message.delete()
        except Exception as e:
            print(f"DEBUG: Ошибка при удалении сообщения: {e}")
    else:
        print("DEBUG: Сообщение уже было удалено пользователем")
    
    # Сбрасываем флаг после завершения таймера
    global review_recently_completed
    review_recently_completed = False
    print("DEBUG: Таймер завершен")

def register_review_handlers(dp):
    """Регистрация обработчиков формы отзыва"""

    @dp.callback_query(F.data.startswith("star_"))
    async def handle_star_selection(callback: types.CallbackQuery, state: FSMContext):
        """Обработка выбора звезды"""
        star_number = int(callback.data.split("_")[1])

        # Получаем текущую выбранную оценку
        data = await state.get_data()
        current_rating = data.get('rating', 0)

        # Если пользователь кликает на уже выбранную звезду, просто отвечаем
        if star_number == current_rating:
            await callback.answer("Эта оценка уже выбрана")
            return

        # Сохраняем выбранную оценку в состоянии
        await state.update_data(rating=star_number)

        # Создаем обновленную клавиатуру с выбранной звездой
        keyboard = await create_rating_keyboard(star_number)

        # Создаем текст с описанием выбранной оценки
        descriptions = ["", "Тильт", "Кринж", "Нормис", "Свага", "Полный фарш!"]
        description_text = f"\n\n<b>Выбранная оценка:</b> {star_number}⭐ - {descriptions[star_number]}"
        new_text = MSG_REVIEW_RATING + description_text

        try:
            await callback.message.edit_text(new_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            # Если сообщение не изменилось, просто отвечаем
            if "message is not modified" in str(e):
                await callback.answer("Оценка уже выбрана")
                return
            else:
                raise e

        try:
            await callback.answer()
        except Exception:
            pass  # Игнорируем ошибки устаревших callback queries

    @dp.callback_query(F.data == "confirm_rating")
    async def handle_rating_confirmation(callback: types.CallbackQuery, state: FSMContext):
        """Обработка подтверждения оценки"""
        data = await state.get_data()
        rating = data.get('rating', 1)

        # Создаем клавиатуру для формы отзыва
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=BUTTON_BACK, callback_data="back_to_rating"),
             types.InlineKeyboardButton(text=BUTTON_CLOSE, callback_data="close_review")]
        ])

        await callback.message.edit_text(MSG_REVIEW_FORM, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(ReviewStates.waiting_for_review_content)
        try:
            await callback.answer()
        except Exception:
            pass  # Игнорируем ошибки устаревших callback queries

    @dp.callback_query(F.data == "back_to_rating")
    async def handle_back_to_rating(callback: types.CallbackQuery, state: FSMContext):
        """Обработка возврата к выбору оценки"""
        data = await state.get_data()
        current_rating = data.get('rating', 0)

        # Создаем клавиатуру выбора оценки с текущей выбранной оценкой
        keyboard = await create_rating_keyboard(current_rating)

        # Создаем текст с описанием выбранной оценки (если есть)
        if current_rating > 0:
            descriptions = ["", "Тильт", "Кринж", "Нормис", "Свага", "Полный фарш!"]
            description_text = f"\n\n<b>Выбранная оценка:</b> {current_rating}⭐ - {descriptions[current_rating]}"
            new_text = MSG_REVIEW_RATING + description_text
        else:
            new_text = MSG_REVIEW_RATING

        await callback.message.edit_text(new_text, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(ReviewStates.waiting_for_rating)
        try:
            await callback.answer()
        except Exception:
            pass  # Игнорируем ошибки устаревших callback queries

    @dp.message(ReviewStates.waiting_for_review_content)
    async def handle_review_content(message: types.Message, state: FSMContext):
        """Обработка текста отзыва"""
        review_text = message.text.strip()
        data = await state.get_data()
        rating = data.get('rating', 5)

        # Получаем счетчик попыток валидации
        validation_attempts = data.get('validation_attempts', 0)

        # Проверяем длину отзыва
        if len(review_text) < 15:
            if validation_attempts == 0:
                # Первая попытка - показываем предупреждение
                warning_msg = await message.answer(
                    MSG_REVIEW_TOO_SHORT.format(length=len(review_text)),
                    parse_mode="HTML"
                )
                # Сохраняем ID предупреждения и ID сообщения пользователя для последующего удаления
                await state.update_data(validation_attempts=1, warning_message_id=warning_msg.message_id, user_message_id=message.message_id)
            else:
                # Последующие попытки - просто удаляем сообщение пользователя
                await safe_delete_message(message)
            return

        if len(review_text) > 300:
            if validation_attempts == 0:
                # Первая попытка - показываем предупреждение
                warning_msg = await message.answer(
                    MSG_REVIEW_TOO_LONG.format(length=len(review_text)),
                    parse_mode="HTML"
                )
                # Сохраняем ID предупреждения и ID сообщения пользователя для последующего удаления
                await state.update_data(validation_attempts=1, warning_message_id=warning_msg.message_id, user_message_id=message.message_id)
            else:
                # Последующие попытки - просто удаляем сообщение пользователя
                await safe_delete_message(message)
            return

        # Отзыв прошел валидацию - удаляем все предыдущие сообщения
        data = await state.get_data()
        warning_message_id = data.get('warning_message_id')
        user_message_id = data.get('user_message_id')

        # Удаляем сообщение с предупреждением, если оно есть
        if warning_message_id:
            try:
                await message.bot.delete_message(message.chat.id, warning_message_id)
            except Exception:
                pass

        # Удаляем предыдущее сообщение пользователя (до предупреждения), если оно есть
        if user_message_id:
            try:
                await message.bot.delete_message(message.chat.id, user_message_id)
            except Exception:
                pass

        # Удаляем сообщение с формой отзыва (сообщение бота "💬 ОСТАВИТЬ ОТЗЫВ"), если оно есть
        review_form_message_id = data.get('review_form_message_id')
        if review_form_message_id:
            try:
                await message.bot.delete_message(message.chat.id, review_form_message_id)
            except Exception:
                pass

        # Удаляем текущее сообщение пользователя с отзывом
        await safe_delete_message(message)

        # Получаем информацию о пользователе
        user_info = {
            'id': message.from_user.id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name
        }

        # Отправляем отзыв на email
        success = await send_review_email(review_text, rating, user_info)

        if success:
            # Устанавливаем флаг, что отзыв был только что отправлен
            global review_recently_completed
            review_recently_completed = True
            await show_success_with_timer(message, duration=10)
        else:
            await message.answer(MSG_REVIEW_ERROR, parse_mode="HTML")

        # Очищаем состояние
        await state.clear()

    @dp.callback_query(F.data == "close_review")
    async def close_review(callback: types.CallbackQuery, state: FSMContext):
        """Закрытие формы отзыва"""
        await safe_delete_message(callback.message)
        await state.clear()
        try:
            await callback.answer()
        except Exception:
            pass  # Игнорируем ошибки устаревших callback queries

    @dp.callback_query(F.data == "close_success")
    async def close_success(callback: types.CallbackQuery):
        """Закрытие сообщения успеха"""
        global current_success_message_id, review_recently_completed
        current_success_message_id = None  # Сбрасываем ID, чтобы таймер знал, что сообщение удалено
        review_recently_completed = False  # Сбрасываем флаг при ручном закрытии
        await safe_delete_message(callback.message)
        try:
            await callback.answer()
        except Exception:
            pass  # Игнорируем ошибки устаревших callback queries
