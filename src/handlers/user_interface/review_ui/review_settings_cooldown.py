"""Управление настройками cooldown для отзывов"""

import asyncio
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.handlers.common.utils import is_admin, safe_delete_message
from src.models import AdminStates
from src.utils.texts import (
    MSG_CANCEL_COOLDOWN_INPUT,
    MSG_CHANGE_COOLDOWN_REQUEST,
    MSG_COOLDOWN_SET_SUCCESS,
    MSG_COOLDOWN_INVALID_RANGE,
    MSG_COOLDOWN_INVALID_FORMAT,
    MSG_RESET_SETTINGS_SUCCESS,
    MSG_REVIEW_SETTINGS_MENU,
    NO_ACCESS_MESSAGE,
    BUTTON_COOLDOWN,
    BUTTON_DAILY_LIMIT,
    BUTTON_RESET_DEFAULT,
    BUTTON_BACK,
    BUTTON_CLOSE,
    BUTTON_CANCEL,
    CALLBACK_ADMIN_SETTINGS,
    CALLBACK_MANAGE_REVIEWS
)
from src.handlers.user_interface.review_logic.review_spam_protection import spam_protection, messages
from src.handlers.user_interface.review_ui.review_settings_daily import _show_simple_message


def register_cooldown_handlers(dp):
    """Регистрация обработчиков для управления cooldown"""

    @dp.callback_query(F.data == "change_cooldown")
    async def change_cooldown_callback(callback: types.CallbackQuery, state: FSMContext):

        if not is_admin(callback.from_user.id):
            try:
                return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
            except Exception:
                return

        await callback.answer()

        cancel_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="cancel_cooldown_input")]]
        )

        chat_id = callback.message.chat.id

        if chat_id in messages:
            msg_id = messages[chat_id]
            try:
                await callback.message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=MSG_CHANGE_COOLDOWN_REQUEST,
                    reply_markup=cancel_kb,
                    parse_mode="HTML"
                )
                await state.set_state(AdminStates.waiting_for_cooldown_value)
                return
            except Exception as e:
                if "message is not modified" in str(e):
                    await state.set_state(AdminStates.waiting_for_cooldown_value)
                    return
                else:
                    del messages[chat_id]

        request_msg = await callback.message.answer(MSG_CHANGE_COOLDOWN_REQUEST, reply_markup=cancel_kb, parse_mode="HTML")
        messages[chat_id] = request_msg.message_id
        await state.set_state(AdminStates.waiting_for_cooldown_value)

    @dp.callback_query(F.data == "cancel_cooldown_input")
    async def cancel_cooldown_input_callback(callback: types.CallbackQuery, state: FSMContext):

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
            await callback.answer(MSG_CANCEL_COOLDOWN_INPUT, show_alert=True)
        except Exception:
            pass
        await state.clear()

    @dp.message(AdminStates.waiting_for_cooldown_value)
    async def handle_cooldown_value(message: types.Message, state: FSMContext):

        if not is_admin(message.from_user.id):
            await state.clear()
            return

        chat_id = message.chat.id

        try:
            value = int(message.text.strip())
            if not 0 <= value <= 1440:
                await _show_simple_message(message, MSG_COOLDOWN_INVALID_RANGE, request_message_id=messages.get(chat_id))
                await state.clear()
                return

            spam_protection.cooldown_minutes = value
            spam_protection.save_settings()

            status = "отключен" if value == 0 else f"установлен на {value} мин"
            await _show_simple_message(message, MSG_COOLDOWN_SET_SUCCESS.format(status=status), request_message_id=messages.get(chat_id))
            await state.clear()

        except ValueError:
            await _show_simple_message(message, MSG_COOLDOWN_INVALID_FORMAT, request_message_id=messages.get(chat_id))
            await state.clear()


def register_reset_handlers(dp):
    """Регистрация обработчиков для сброса настроек"""

    @dp.callback_query(F.data == "reset_settings")
    async def reset_settings_callback(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            try:
                return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
            except Exception:
                return

        spam_protection.cooldown_minutes = 0
        spam_protection.max_reviews_per_day = 3
        spam_protection.save_settings()

        try:
            await callback.answer(MSG_RESET_SETTINGS_SUCCESS, show_alert=True)
        except Exception:
            pass
        await safe_delete_message(callback.message)
        await show_review_settings_menu(callback.message)


async def show_review_settings_menu(message: types.Message):
    """Показывает меню настройки параметров защиты от спама"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    text = MSG_REVIEW_SETTINGS_MENU.format(
        cooldown_status="отключен" if spam_protection.cooldown_minutes == 0 else f"{spam_protection.cooldown_minutes} мин",
        max_reviews=spam_protection.max_reviews_per_day
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BUTTON_COOLDOWN, callback_data="change_cooldown"),
             InlineKeyboardButton(text=BUTTON_DAILY_LIMIT, callback_data="change_daily_limit")],
            [InlineKeyboardButton(text=BUTTON_RESET_DEFAULT, callback_data="reset_settings")],
            [InlineKeyboardButton(text=BUTTON_BACK, callback_data=CALLBACK_MANAGE_REVIEWS),
             InlineKeyboardButton(text=BUTTON_CLOSE, callback_data=CALLBACK_ADMIN_SETTINGS)]
        ]
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
