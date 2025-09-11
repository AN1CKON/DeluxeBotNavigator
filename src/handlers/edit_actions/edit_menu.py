"""Главное меню редактирования кнопки"""

from aiogram import types
from aiogram.fsm.context import FSMContext
from src.database import get_menu_item, get_menu_items
from src.utils.texts import *
from src.handlers.common.utils import get_style_display_text

async def show_edit_button_menu(message: types.Message, item_id: int, state: FSMContext):
    """Показать меню редактирования для выбранной кнопки"""
    
    # Получаем данные кнопки
    menu_item = get_menu_item(item_id)
    if not menu_item:
        return await message.answer(MSG_ERROR_ITEM_NOT_FOUND)
    
    # Получаем название родительского раздела
    parent_name = "Главное меню"
    if menu_item[1]:  # parent_id
        parent_item = get_menu_item(menu_item[1])
        if parent_item:
            parent_name = parent_item[2]  # title
    
    # Определяем наличие изображения
    has_image_exists = menu_item[6] and menu_item[6].strip()  # image_path находится под индексом 6
    has_image = "✅ Есть" if has_image_exists else "❌ Нет"
    
    # Формируем информационный текст используя шаблоны
    button_name = menu_item[2]  # title
    section_name = parent_name
    style_name = get_style_display_text(menu_item[4])  # content_type
    
    # Используем шаблон для информации о кнопке
    item_info = ITEM_INFO_TEMPLATE.format(
        button_name=button_name,
        section_name=section_name,
        style_name=style_name,
        has_image=has_image
    )
    
    # Используем шаблон для всего меню редактирования
    info_text = EDIT_MENU_TEMPLATE.format(item_info=item_info)
    
    # Создаём клавиатуру
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text=BUTTON_EDIT_RENAME, callback_data=f"edit_action_rename:{item_id}"),
            types.InlineKeyboardButton(text=BUTTON_EDIT_STYLE, callback_data=f"edit_action_style:{item_id}")
        ],
        [
            types.InlineKeyboardButton(text=BUTTON_EDIT_IMAGE, callback_data=f"edit_action_image:{item_id}")
        ],
        [
            types.InlineKeyboardButton(text=BUTTON_BACK, callback_data=CALLBACK_ADMIN_EDIT),
            types.InlineKeyboardButton(text=BUTTON_CANCEL, callback_data=CALLBACK_ADMIN_CANCEL)
        ]
    ])
    
    await message.answer(info_text, reply_markup=keyboard, parse_mode="HTML")
