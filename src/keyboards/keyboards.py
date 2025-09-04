"""Основные клавиатуры для навигации DeluxeBotNavigator"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..database.db import get_menu_items, get_menu_item, has_children
from ..config.config import ADMIN_ID
from ..utils.texts import *

# ========== ОСНОВНЫЕ КЛАВИАТУРЫ ==========

def build_keyboard(parent_id=None, user_id: int = None) -> InlineKeyboardMarkup:
    """Основная навигационная клавиатура с возможной кнопкой админ-панели"""
    kb = []
    
    # Добавляем элементы меню
    items = get_menu_items(parent_id)
    for item_id, title in items:
        if has_children(item_id):
            display_title = f"{FOLDER_PREFIX}{title}"
        else:
            display_title = title
        
        item = get_menu_item(item_id)
        if item[4] == "post_link" or item[4] == "link":
            # Создаем URL-кнопку для ссылок
            kb.append([InlineKeyboardButton(text=display_title, url=item[3])])
        else:
            kb.append([InlineKeyboardButton(text=display_title, callback_data=f"nav:{item_id}")])
    
    # Добавляем кнопку админ-панели в корневом меню для администратора
    if parent_id is None and user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text=BUTTON_ADMIN_PANEL, callback_data="open_admin_panel")])
    
    # Кнопка "Назад"
    if parent_id is not None:
        parent_item = get_menu_item(parent_id)
        if parent_item and parent_item[1] is not None:
            kb.append([InlineKeyboardButton(text=BUTTON_BACK, callback_data=f"nav:{parent_item[1]}")])
        else:
            kb.append([InlineKeyboardButton(text=BUTTON_MAIN_MENU, callback_data="nav:root")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def close_text_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для закрытия текстовых сообщений"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_CLOSE, callback_data="close_text")]
    ])

def welcome_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для приветственного сообщения"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_WELCOME_DONE, callback_data="welcome_done")],
        [InlineKeyboardButton(text=BUTTON_WELCOME_MOBILE, callback_data="welcome_mobile")]
    ])

def welcome_mobile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для мобильной инструкции"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_WELCOME_DONE, callback_data="welcome_done")],
        [InlineKeyboardButton(text=BUTTON_WELCOME_PC, callback_data="welcome_pc")]
    ])
