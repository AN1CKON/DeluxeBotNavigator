"""Обработчик добавления пунктов меню"""

import asyncio
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from ..database.db import add_menu_item
from ..models.states import MenuState
from .utils import (
    safe_delete_message, delete_user_messages, send_notification_and_cleanup, validate_url
)
from ..keyboards.keyboards_admin import (
    parent_menu_keyboard, admin_keyboard, back_cancel_keyboard, style_keyboard
)
from ..config.config import get_image_path
from ..utils.texts import *

async def cleanup_invalid_url_messages(user_message, error_message, delay: int):
    """Удаляет сообщение пользователя и уведомление об ошибке с динамическим таймером"""
    try:
        # Показываем обратный отсчёт
        for remaining in range(delay, 0, -1):
            countdown_text = f"❌ Некорректная ссылка! Введите корректный URL: ({remaining})"
            await error_message.edit_text(countdown_text)
            await asyncio.sleep(1)
        
        # Удаляем сообщения
        await user_message.delete()
        await error_message.delete()
    except Exception:
        # Если произошла ошибка, просто удаляем сообщения без таймера
        try:
            await user_message.delete()
        except:
            pass
        try:
            await error_message.delete()
        except:
            pass

def register_admin_add(dp):
    async def notify_and_return_to_panel(message):
        """Уведомляет об успехе и возвращает в админ-панель"""
        await send_notification_and_cleanup(message, MSG_ITEM_ADDED)
        photo = FSInputFile(get_image_path("admin.JPG"))
        await message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())

    # --- Callback handlers ---
    @dp.callback_query(F.data == "back_to_title")
    async def back_to_title(callback: types.CallbackQuery, state: FSMContext):
        """Возврат к вводу названия"""
        await safe_delete_message(callback.message)
        await state.set_state(MenuState.waiting_for_title)
        await callback.message.answer(MSG_ENTER_TITLE, reply_markup=back_cancel_keyboard("admin_add"))

    @dp.callback_query(F.data == "back_to_style")
    async def back_to_style(callback: types.CallbackQuery, state: FSMContext):
        """Возврат к выбору стиля"""
        await safe_delete_message(callback.message)
        await state.set_state(MenuState.waiting_for_content_type)
        await callback.message.answer(MSG_CHOOSE_STYLE, reply_markup=style_keyboard())

    @dp.callback_query(F.data == "admin_add")
    async def admin_add_start(callback: types.CallbackQuery, state: FSMContext):
        """Начало процесса добавления"""
        await safe_delete_message(callback.message)
        await state.clear()
        await state.update_data(mode="add")
        await state.set_state(MenuState.waiting_for_parent)
        await callback.message.answer(MSG_CHOOSE_PARENT, reply_markup=parent_menu_keyboard())

    @dp.callback_query(F.data.startswith("set_parent:"))
    async def set_parent(callback: types.CallbackQuery, state: FSMContext):
        """Установка родительского элемента"""
        parent_id = int(callback.data.split(":")[1]) or None
        await safe_delete_message(callback.message)
        await state.update_data(parent_id=parent_id)
        await state.set_state(MenuState.waiting_for_title)
        await callback.message.answer(MSG_ENTER_TITLE, reply_markup=back_cancel_keyboard("admin_add"))

    # --- Message handlers ---
    @dp.message(MenuState.waiting_for_title)
    async def handle_title(message: types.Message, state: FSMContext):
        """Обработка ввода названия"""
        if not message.text:
            return await message.answer(MSG_ERROR_TEXT_ONLY)
            
        await state.update_data(title=message.text.strip())
        await delete_user_messages(message.bot, message.chat.id, message.message_id)
        await state.set_state(MenuState.waiting_for_content_type)
        await message.answer(MSG_CHOOSE_STYLE, reply_markup=style_keyboard())

    @dp.callback_query(F.data.startswith("ctype:"))
    async def handle_content_type_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработка выбора типа контента"""
        await safe_delete_message(callback.message)
        content_type = callback.data.replace("ctype:", "")
        data = await state.get_data()
        await state.update_data(content_type=content_type)
        
        if content_type == "menu":
            # Создаем пункт меню сразу
            add_menu_item(
                data["title"],
                content=None,
                content_type="menu",
                parent_id=data.get("parent_id")
            )
            await notify_and_return_to_panel(callback.message)
            await state.clear()
            return
            
        if content_type == "attachment":
            # Функционал в разработке
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BUTTON_BACK, callback_data="back_to_style")]
            ])
            await callback.message.answer(MSG_FEATURE_IN_DEVELOPMENT, reply_markup=kb)
            return
            
        # Запрашиваем контент
        await state.set_state(MenuState.waiting_for_content)
        msg = {
            "text": MSG_ENTER_CONTENT_TEXT,
            "link": MSG_ENTER_CONTENT_LINK,
            "post_link": MSG_ENTER_CONTENT_LINK
        }.get(content_type, MSG_ENTER_CONTENT_TEXT)
        await callback.message.answer(msg, reply_markup=back_cancel_keyboard("back_to_style"))

    @dp.message(MenuState.waiting_for_content)
    async def handle_content(message: types.Message, state: FSMContext):
        """Обработка ввода контента"""
        if not message.text:
            return await message.answer(MSG_ERROR_TEXT_ONLY)
            
        data = await state.get_data()
        content_type = data.get("content_type")
        content = message.text.strip()

        # Валидация контента
        if content_type in ["link", "post_link"] and not validate_url(content):
            # Отправляем временное уведомление об ошибке
            error_msg = await message.answer(MSG_INVALID_URL)
            # Создаём асинхронную задачу для удаления сообщений через 3 секунды
            asyncio.create_task(cleanup_invalid_url_messages(message, error_msg, 3))
            return

        # Удаляем пользовательское сообщение
        await delete_user_messages(message.bot, message.chat.id, message.message_id)

        # Создаем пункт меню
        add_menu_item(
            data["title"],
            content=content,
            content_type=content_type,
            parent_id=data.get("parent_id")
        )
        
        await notify_and_return_to_panel(message)
        await state.clear()

    @dp.callback_query(F.data == "admin_panel")
    async def back_to_admin_panel(callback: types.CallbackQuery, state: FSMContext = None):
        """Возврат в админ-панель"""
        await safe_delete_message(callback.message)
        if state:
            await state.clear()
        photo = FSInputFile(get_image_path("admin.JPG"))
        await callback.message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())
