"""Управление настройками дневного лимита для отзывов"""

import asyncio
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.handlers.common.utils import is_admin, safe_delete_message
from src.models import AdminStates
from src.utils.texts import (
    MSG_CHANGE_DAILY_LIMIT_REQUEST,
    MSG_DAILY_LIMIT_SET_SUCCESS,
    MSG_DAILY_LIMIT_INVALID_RANGE,
    MSG_DAILY_LIMIT_INVALID_FORMAT,
    NO_ACCESS_MESSAGE,
    MSG_CANCEL_DAILY_LIMIT_INPUT,
    BUTTON_CANCEL
)
from src.handlers.user_interface.review_logic.review_spam_protection import spam_protection, messages


async def _show_simple_message(message: types.Message, text: str, request_message_id: int = None):
    """Показывает простое сообщение и удаляет связанные сообщения"""
    # global messages  # Убираем, так как messages теперь импортирован

    msg = await message.answer(text)
    await asyncio.sleep(2)
    await safe_delete_message(msg)
    await safe_delete_message(message)
    if request_message_id:
        try:
            await message.bot.delete_message(message.chat.id, request_message_id)
        except Exception:
            pass

        if message.chat.id in messages:
            del messages[message.chat.id]


def register_daily_limit_handlers(dp):
    """Регистрация обработчиков для управления дневным лимитом"""

    @dp.callback_query(F.data == "change_daily_limit")
    async def change_daily_limit_callback(callback: types.CallbackQuery, state: FSMContext):
        # global messages  # Убираем, так как messages теперь импортирован

        if not is_admin(callback.from_user.id):
            try:
                return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
            except Exception:
                return

        await callback.answer()

        cancel_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="cancel_daily_limit_input")]]
        )

        chat_id = callback.message.chat.id

        if chat_id in messages:
            msg_id = messages[chat_id]
            try:
                await callback.message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=MSG_CHANGE_DAILY_LIMIT_REQUEST,
                    reply_markup=cancel_kb,
                    parse_mode="HTML"
                )
                await state.set_state(AdminStates.waiting_for_daily_limit_value)
                return
            except Exception as e:
                if "message is not modified" in str(e):
                    await state.set_state(AdminStates.waiting_for_daily_limit_value)
                    return
                else:
                    del messages[chat_id]

        request_msg = await callback.message.answer(MSG_CHANGE_DAILY_LIMIT_REQUEST, reply_markup=cancel_kb, parse_mode="HTML")
        messages[chat_id] = request_msg.message_id
        await state.set_state(AdminStates.waiting_for_daily_limit_value)

    @dp.message(AdminStates.waiting_for_daily_limit_value)
    async def handle_daily_limit_value(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await state.clear()
            return

        chat_id = message.chat.id

        try:
            value = int(message.text.strip())
            if not 1 <= value <= 50:
                await _show_simple_message(message, MSG_DAILY_LIMIT_INVALID_RANGE, messages.get(chat_id))
                await state.clear()
                return

            spam_protection.max_reviews_per_day = value
            spam_protection.save_settings()

            await _show_simple_message(message, MSG_DAILY_LIMIT_SET_SUCCESS.format(value=value), messages.get(chat_id))
            await state.clear()

        except ValueError:
            await _show_simple_message(message, MSG_DAILY_LIMIT_INVALID_FORMAT, messages.get(chat_id))
            await state.clear()


def register_cancel_handlers(dp):
    """Регистрация обработчиков для отмены ввода"""

    @dp.callback_query(F.data == "cancel_daily_limit_input")
    async def cancel_daily_limit_input_callback(callback: types.CallbackQuery, state: FSMContext):
        # global messages  # Убираем, так как messages теперь импортирован

        if not is_admin(callback.from_user.id):
            try:
                return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
            except Exception:
                return

        chat_id = callback.message.chat.id

        if chat_id in messages:
            try:
                await callback.message.bot.delete_message(chat_id, messages[chat_id])
            except Exception:
                pass
            del messages[chat_id]

        try:
            await callback.answer(MSG_CANCEL_DAILY_LIMIT_INPUT, show_alert=True)
        except Exception:
            pass
        await state.clear()
