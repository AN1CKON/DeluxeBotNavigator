"""Обработчик изменения изображения кнопки"""

import os
import uuid
from typing import Optional, Tuple
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from ...database.db import get_menu_item, update_menu_item_image
from ...utils.texts import *
from ...models.states import MenuState
from ..utils import safe_delete_message, is_admin, send_notification_and_cleanup, delete_user_messages
from ...config.config import MEDIA_PATH

# Константы
IMAGE_PATH_INDEX = 9
MAX_IMAGE_SIZE = 10 * 1024 * 1024
BUTTON_IMAGES_DIR = "button_images"

# Вспомогательные функции
def has_image(menu_item) -> bool:
    """Проверяет наличие изображения у пункта меню"""
    return bool(menu_item and menu_item[IMAGE_PATH_INDEX] and menu_item[IMAGE_PATH_INDEX].strip())

def get_image_path(menu_item) -> Optional[str]:
    """Возвращает полный путь к изображению"""
    return os.path.join(MEDIA_PATH, menu_item[IMAGE_PATH_INDEX]) if has_image(menu_item) else None

def generate_image_filename(item_id: int) -> str:
    """Генерирует уникальное имя файла"""
    return f"button_{item_id}_{uuid.uuid4().hex[:8]}.jpg"

def get_item_info(menu_item) -> Tuple[str, str, str, bool]:
    """Возвращает информацию о пункте меню"""
    button_name = menu_item[2]
    parent_name = "Главное меню"
    if menu_item[1]:  # parent_id
        from ...database.db import get_menu_item as get_parent_item
        parent_item = get_parent_item(menu_item[1])
        if parent_item:
            parent_name = parent_item[2]
    
    from ..utils import get_style_display_text
    style_name = get_style_display_text(menu_item[4])
    item_has_image = has_image(menu_item)
    
    return button_name, parent_name, style_name, item_has_image

async def validate_admin_and_item(callback: types.CallbackQuery, state: FSMContext) -> Optional[int]:
    """Валидация админа и получение item_id"""
    if not is_admin(callback.from_user.id):
        await callback.answer(MSG_ERROR_ACCESS_DENIED, show_alert=True)
        return None
    
    data = await state.get_data()
    item_id = data.get('editing_item_id')
    if not item_id:
        await callback.answer(MSG_ERROR_ITEM_NOT_FOUND, show_alert=True)
        return None
    
    return item_id

def register_image_action(dp):
    """Регистрация обработчиков изменения изображения"""
    
    @dp.callback_query(F.data.startswith("edit_action_image:"))
    async def handle_image_action(callback: types.CallbackQuery, state: FSMContext):
        """Главный обработчик изменения изображения"""
        if not is_admin(callback.from_user.id):
            await callback.answer(MSG_ERROR_ACCESS_DENIED, show_alert=True)
            return
        
        await safe_delete_message(callback.message)
        
        try:
            item_id = int(callback.data.split(":")[1])
            menu_item = get_menu_item(item_id)
            if not menu_item:
                await callback.answer(MSG_ERROR_ITEM_NOT_FOUND, show_alert=True)
                return
            
            await state.update_data(editing_item_id=item_id)
            await show_image_management_menu(callback.message, menu_item, state)
        except (ValueError, IndexError):
            await callback.answer(MSG_ERROR_ITEM_NOT_FOUND, show_alert=True)
    
    @dp.callback_query(F.data.startswith("image_action:"))
    async def handle_image_menu_action(callback: types.CallbackQuery, state: FSMContext):
        """Обработка действий в меню изображений"""
        item_id = await validate_admin_and_item(callback, state)
        if not item_id:
            return
        
        action = callback.data.split(":")[1]
        
        if action == "add_change":
            await handle_add_change_image(callback, state, item_id)
        elif action == "delete":
            await handle_delete_confirmation(callback, state, item_id)
        elif action == "confirm_delete":
            await handle_delete_image(callback, state, item_id)
        elif action == "back":
            await safe_delete_message(callback.message)
            from . import edit_menu
            await edit_menu.show_edit_button_menu(callback.message, item_id, state)
    
    @dp.callback_query(F.data.startswith("image_upload_cancel:"))
    async def handle_image_upload_cancel(callback: types.CallbackQuery, state: FSMContext):
        """Отмена загрузки изображения"""
        if not is_admin(callback.from_user.id):
            await callback.answer(MSG_ERROR_ACCESS_DENIED, show_alert=True)
            return
        
        item_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        await state.clear()
        
        menu_item = get_menu_item(item_id)
        if menu_item:
            await state.update_data(editing_item_id=item_id)
            await show_image_management_menu(callback.message, menu_item, state)
    
    @dp.message(MenuState.waiting_for_image_upload)
    async def handle_image_upload(message: types.Message, state: FSMContext):
        """Обработка загрузки изображения"""
        if not is_admin(message.from_user.id):
            await message.answer(MSG_ERROR_ACCESS_DENIED)
            return
        
        if not message.photo:
            await message.answer(MSG_ERROR_INVALID_IMAGE_FORMAT)
            return
        
        data = await state.get_data()
        item_id = data.get('editing_item_id')
        if not item_id:
            await message.answer(MSG_ERROR_ITEM_NOT_FOUND)
            return
        
        try:
            await process_image_upload(message, state, item_id)
        except Exception as e:
            await message.answer(MSG_ERROR_IMAGE_UPLOAD_FAILED)
            print(f"Ошибка загрузки: {e}")

async def process_image_upload(message: types.Message, state: FSMContext, item_id: int):
    """Обрабатывает загрузку изображения"""
    photo = message.photo[-1]
    
    if photo.file_size > MAX_IMAGE_SIZE:
        await message.answer(MSG_ERROR_IMAGE_TOO_LARGE)
        return
    
    # Подготовка путей
    images_dir = os.path.join(MEDIA_PATH, BUTTON_IMAGES_DIR)
    os.makedirs(images_dir, exist_ok=True)
    
    filename = generate_image_filename(item_id)
    file_path = os.path.join(images_dir, filename)
    relative_path = os.path.join(BUTTON_IMAGES_DIR, filename)
    
    try:
        # Загрузка файла
        file_info = await message.bot.get_file(photo.file_id)
        await message.bot.download_file(file_info.file_path, file_path)
        
        if update_menu_item_image(item_id, relative_path):
            # Очистка сообщений
            state_data = await state.get_data()
            upload_message_id = state_data.get('upload_message_id')
            
            await delete_user_messages(message.bot, message.chat.id, message.message_id, 1)
            if upload_message_id:
                try:
                    await message.bot.delete_message(message.chat.id, upload_message_id)
                except:
                    pass
            
            await send_notification_and_cleanup(message, MSG_SUCCESS_IMAGE_UPLOADED)
            
            # Возврат к меню
            menu_item = get_menu_item(item_id)
            if menu_item:
                await show_image_management_menu(message, menu_item, state)
            else:
                await state.clear()
        else:
            if os.path.exists(file_path):
                os.remove(file_path)
            await message.answer(MSG_ERROR_IMAGE_UPLOAD_FAILED)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e

async def show_image_management_menu(message: types.Message, menu_item, state: FSMContext):
    """Показывает меню управления изображением"""
    button_name, parent_name, style_name, item_has_image = get_item_info(menu_item)
    
    # Формируем текст и клавиатуру
    item_info = ITEM_INFO_TEMPLATE.format(
        button_name=button_name,
        section_name=parent_name,
        style_name=style_name,
        has_image="✅ Есть" if item_has_image else "❌ Нет"
    )
    text = IMAGE_MENU_TEMPLATE.format(item_info=item_info)
    
    # Создаём клавиатуру
    keyboard_buttons = []
    if item_has_image:
        keyboard_buttons.extend([
            [types.InlineKeyboardButton(text=BUTTON_IMAGE_CHANGE, callback_data="image_action:add_change")],
            [types.InlineKeyboardButton(text=BUTTON_IMAGE_DELETE, callback_data="image_action:delete")]
        ])
    else:
        keyboard_buttons.append([types.InlineKeyboardButton(text=BUTTON_IMAGE_ADD, callback_data="image_action:add_change")])
    
    keyboard_buttons.append([types.InlineKeyboardButton(text=BUTTON_BACK, callback_data="image_action:back")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправка сообщения
    if item_has_image:
        image_path = get_image_path(menu_item)
        if image_path and os.path.exists(image_path):
            try:
                photo = types.FSInputFile(image_path)
                await message.answer_photo(photo=photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
                return
            except Exception as e:
                print(f"Ошибка отправки изображения: {e}")
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

async def handle_add_change_image(callback: types.CallbackQuery, state: FSMContext, item_id: int):
    """Добавление/изменение изображения"""
    await safe_delete_message(callback.message)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=BUTTON_CANCEL, callback_data=f"image_upload_cancel:{item_id}")]
    ])
    
    upload_message = await callback.message.answer(MSG_REQUEST_IMAGE_UPLOAD, reply_markup=keyboard, parse_mode="HTML")
    await state.update_data(upload_message_id=upload_message.message_id)
    await state.set_state(MenuState.waiting_for_image_upload)

async def handle_delete_confirmation(callback: types.CallbackQuery, state: FSMContext, item_id: int):
    """Подтверждение удаления изображения"""
    menu_item = get_menu_item(item_id)
    if not menu_item or not has_image(menu_item):
        await callback.answer("❌ Изображение не найдено", show_alert=True)
        return
    
    await safe_delete_message(callback.message)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text=BUTTON_CONFIRM_DELETE_IMAGE, callback_data="image_action:confirm_delete"),
            types.InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="image_action:back")
        ]
    ])
    
    await callback.message.answer(MSG_CONFIRM_DELETE_IMAGE, reply_markup=keyboard, parse_mode="HTML")

async def handle_delete_image(callback: types.CallbackQuery, state: FSMContext, item_id: int):
    """Удаление изображения"""
    menu_item = get_menu_item(item_id)
    if not menu_item or not has_image(menu_item):
        await callback.answer("❌ Изображение не найдено", show_alert=True)
        return
    
    try:
        # Удаление файла
        image_path = get_image_path(menu_item)
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
        
        if update_menu_item_image(item_id, None):
            await safe_delete_message(callback.message)
            await send_notification_and_cleanup(callback.message, MSG_SUCCESS_IMAGE_DELETED)
            
            updated_menu_item = get_menu_item(item_id)
            if updated_menu_item:
                await show_image_management_menu(callback.message, updated_menu_item, state)
            else:
                await state.clear()
        else:
            await callback.answer(MSG_ERROR_IMAGE_UPLOAD_FAILED, show_alert=True)
    except Exception as e:
        print(f"Ошибка удаления: {e}")
        await callback.answer(MSG_ERROR_IMAGE_UPLOAD_FAILED, show_alert=True)
