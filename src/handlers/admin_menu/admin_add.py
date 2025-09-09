"""Обработчик добавления пунктов меню"""

import asyncio
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from ...database import add_menu_item, update_menu_item_image, get_db
import os
from ...models.states import MenuState
from ..common.utils import (
    safe_delete_message, delete_user_messages, send_notification_and_cleanup, validate_url
)
from ...keyboards.keyboards_admin import (
    parent_menu_keyboard, admin_keyboard, back_cancel_keyboard, style_keyboard, image_choice_keyboard
)
from ...config.config import get_image_path, MEDIA_PATH
from ...utils.texts import *

# Константы для работы с изображениями
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
BUTTON_IMAGES_DIR = "button_images"

def generate_image_filename(item_id: int) -> str:
    """Генерирует имя файла для изображения кнопки"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"button_{item_id}_{timestamp}.jpg"

async def cleanup_invalid_url_messages(user_message, error_message, delay: int):
    """Удаляет сообщение пользователя и уведомление об ошибке с динамическим таймером"""
    try:
        # Показываем обратный отсчёт
        for remaining in range(delay, 0, -1):
            countdown_text = f"❌ Некорректная ссылка! Введите корректный URL: ({remaining})"
            await error_message.edit_text(countdown_text, parse_mode="HTML")
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
        await message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard(), parse_mode="HTML")

    # --- Callback handlers ---
    @dp.callback_query(F.data == "back_to_title")
    async def back_to_title(callback: types.CallbackQuery, state: FSMContext):
        """Возврат к вводу названия"""
        await safe_delete_message(callback.message)
        await state.set_state(MenuState.waiting_for_title)
        await callback.message.answer(MSG_ENTER_TITLE, reply_markup=back_cancel_keyboard("admin_add"), parse_mode="HTML")

    @dp.callback_query(F.data == "back_to_style")
    async def back_to_style(callback: types.CallbackQuery, state: FSMContext):
        """Возврат к выбору стиля"""
        await safe_delete_message(callback.message)
        await state.set_state(MenuState.waiting_for_content_type)
        await callback.message.answer(MSG_CHOOSE_STYLE, reply_markup=style_keyboard(), parse_mode="HTML")

    @dp.callback_query(F.data == "admin_add")
    async def admin_add_start(callback: types.CallbackQuery, state: FSMContext):
        """Начало процесса добавления"""
        await safe_delete_message(callback.message)
        await state.clear()
        await state.update_data(mode="add")
        await state.set_state(MenuState.waiting_for_parent)
        await callback.message.answer(MSG_CHOOSE_PARENT, reply_markup=parent_menu_keyboard(), parse_mode="HTML")

    @dp.callback_query(F.data.startswith("set_parent:"))
    async def set_parent(callback: types.CallbackQuery, state: FSMContext):
        """Установка родительского элемента"""
        parent_id = int(callback.data.split(":")[1]) or None
        await safe_delete_message(callback.message)
        await state.update_data(parent_id=parent_id)
        await state.set_state(MenuState.waiting_for_title)
        await callback.message.answer(MSG_ENTER_TITLE, reply_markup=back_cancel_keyboard("admin_add"), parse_mode="HTML")

    # --- Message handlers ---
    @dp.message(MenuState.waiting_for_title)
    async def handle_title(message: types.Message, state: FSMContext):
        """Обработка ввода названия"""
        if not message.text:
            return await message.answer(MSG_ERROR_TEXT_ONLY, parse_mode="HTML")
            
        await state.update_data(title=message.text.strip())
        await delete_user_messages(message.bot, message.chat.id, message.message_id)
        await state.set_state(MenuState.waiting_for_content_type)
        await message.answer(MSG_CHOOSE_STYLE, reply_markup=style_keyboard(), parse_mode="HTML")

    @dp.callback_query(F.data.startswith("ctype:"))
    async def handle_content_type_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработка выбора типа контента"""
        await safe_delete_message(callback.message)
        content_type = callback.data.replace("ctype:", "")
        data = await state.get_data()
        await state.update_data(content_type=content_type)
        
        if content_type == "menu":
            # Для меню сразу переходим к выбору изображения
            await state.set_state(MenuState.waiting_for_image)
            await callback.message.answer(MSG_CHOOSE_IMAGE_STEP, reply_markup=image_choice_keyboard(), parse_mode="HTML")
            return
            
        if content_type == "attachment":
            # Функционал в разработке
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BUTTON_BACK, callback_data="back_to_style")]
            ])
            await callback.message.answer(MSG_FEATURE_IN_DEVELOPMENT, reply_markup=kb, parse_mode="HTML")
            return
            
        if content_type == "review":
            # Для отзывов сразу переходим к выбору изображения
            await state.set_state(MenuState.waiting_for_image)
            await callback.message.answer(MSG_CHOOSE_IMAGE_STEP, reply_markup=image_choice_keyboard(), parse_mode="HTML")
            return
            
        # Для остальных типов сначала запрашиваем контент
        await state.set_state(MenuState.waiting_for_content)
        msg = {
            "text": MSG_ENTER_CONTENT_TEXT,
            "link": MSG_ENTER_CONTENT_LINK,
            "post_link": MSG_ENTER_CONTENT_LINK
        }.get(content_type, MSG_ENTER_CONTENT_TEXT)
        await callback.message.answer(msg, reply_markup=back_cancel_keyboard("back_to_style"), parse_mode="HTML")

    @dp.callback_query(F.data == "skip_image")
    async def skip_image(callback: types.CallbackQuery, state: FSMContext):
        """Пропуск добавления изображения"""
        await safe_delete_message(callback.message)
        data = await state.get_data()
        content_type = data.get("content_type")
        content = data.get("content", "")  # Получаем введенный ранее контент
        
        # Создаем пункт меню без изображения
        add_menu_item(
            parent_id=data.get("parent_id"),
            title=data["title"],
            content=content,
            content_type=content_type
        )
        await notify_and_return_to_panel(callback.message)
        await state.clear()

    @dp.callback_query(F.data == "back_to_image")
    async def back_to_image(callback: types.CallbackQuery, state: FSMContext):
        """Возврат к выбору изображения"""
        await safe_delete_message(callback.message)
        await state.set_state(MenuState.waiting_for_image)
        await callback.message.answer(MSG_CHOOSE_IMAGE_STEP, reply_markup=image_choice_keyboard(), parse_mode="HTML")

    @dp.message(MenuState.waiting_for_image)
    async def handle_image_upload(message: types.Message, state: FSMContext):
        """Обработка загрузки изображения"""
        if not message.photo:
            # Если это не изображение, показываем инструкцию
            await message.answer(MSG_REQUEST_IMAGE_UPLOAD, reply_markup=image_choice_keyboard(), parse_mode="HTML")
            return
        
        photo = message.photo[-1]
        
        if photo.file_size > MAX_IMAGE_SIZE:
            await message.answer(MSG_ERROR_IMAGE_TOO_LARGE, parse_mode="HTML")
            return

        data = await state.get_data()
        content_type = data.get("content_type")
        content = data.get("content", "")  # Получаем введенный ранее контент
        
        # Создаем элемент меню сначала, чтобы получить ID
        item_id = add_menu_item(
            parent_id=data.get("parent_id"),
            title=data["title"],
            content=content,
            content_type=content_type
        )
        
        if not item_id:
            await message.answer("❌ Ошибка создания элемента меню", parse_mode="HTML")
            return
        
        # Сохраняем изображение
        try:
            # Подготовка путей
            images_dir = os.path.join(MEDIA_PATH, BUTTON_IMAGES_DIR)
            os.makedirs(images_dir, exist_ok=True)
            
            filename = generate_image_filename(item_id)
            file_path = os.path.join(images_dir, filename)
            relative_path = os.path.join(BUTTON_IMAGES_DIR, filename)
            
            # Загрузка файла
            file_info = await message.bot.get_file(photo.file_id)
            await message.bot.download_file(file_info.file_path, file_path)
            
            # Обновляем запись в БД с изображением
            if update_menu_item_image(item_id, relative_path):
                # Удаляем сообщение пользователя
                await delete_user_messages(message.bot, message.chat.id, message.message_id)
                
                # Завершаем процесс
                await send_notification_and_cleanup(message, MSG_ITEM_ADDED)
                photo = FSInputFile(get_image_path("admin.JPG"))
                await message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard(), parse_mode="HTML")
                await state.clear()
            else:
                await message.answer("❌ Ошибка привязки изображения", parse_mode="HTML")
                
        except Exception as e:
            await message.answer(MSG_ERROR_IMAGE_UPLOAD_FAILED, parse_mode="HTML")
            print(f"Ошибка загрузки изображения: {e}")

    @dp.message(MenuState.waiting_for_content)
    async def handle_content(message: types.Message, state: FSMContext):
        """Обработка ввода контента"""
        if not message.text:
            return await message.answer(MSG_ERROR_TEXT_ONLY, parse_mode="HTML")
            
        data = await state.get_data()
        content_type = data.get("content_type")
        content = message.text.strip()

        # Валидация контента
        if content_type in ["link", "post_link"] and not validate_url(content):
            # Отправляем временное уведомление об ошибке
            error_msg = await message.answer(MSG_INVALID_URL, parse_mode="HTML")
            # Создаём асинхронную задачу для удаления сообщений через 3 секунды
            asyncio.create_task(cleanup_invalid_url_messages(message, error_msg, 3))
            return

        # Удаляем пользовательское сообщение
        await delete_user_messages(message.bot, message.chat.id, message.message_id)

        # Сохраняем контент в состоянии для дальнейшего использования
        await state.update_data(content=content)
        
        # Для ссылок пропускаем выбор изображения и сразу создаем элемент меню
        if content_type in ["link", "post_link"]:
            # Создаем пункт меню без изображения
            add_menu_item(
                parent_id=data.get("parent_id"),
                title=data["title"],
                content=content,
                content_type=content_type
            )
            await notify_and_return_to_panel(message)
            await state.clear()
            return
        
        # Для остальных типов переходим к выбору изображения
        await state.set_state(MenuState.waiting_for_image)
        await message.answer(MSG_CHOOSE_IMAGE_STEP, reply_markup=image_choice_keyboard(), parse_mode="HTML")

    @dp.callback_query(F.data == "admin_panel")
    async def back_to_admin_panel(callback: types.CallbackQuery, state: FSMContext = None):
        """Возврат в админ-панель"""
        await safe_delete_message(callback.message)
        if state:
            await state.clear()
        photo = FSInputFile(get_image_path("admin.JPG"))
        await callback.message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard(), parse_mode="HTML")
