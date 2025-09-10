"""Основные клавиатуры для навигации DeluxeBotNavigator"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.database import get_menu_items, get_menu_item, has_children
from src.utils import is_admin
from src.utils.texts import *

# ========== ОСНОВНЫЕ КЛАВИАТУРЫ ==========

def build_keyboard(parent_id=None, user_id: int = None) -> InlineKeyboardMarkup:
    """Основная навигационная клавиатура с поддержкой новой группировки и кнопкой админ-панели"""
    kb = []
    
    # Используем новую функцию для получения упорядоченных элементов
    from ..database.positioning.core import get_ordered_items, get_button_groups
    
    # Получаем упорядоченный список элементов
    items = get_ordered_items(parent_id)
    groups = get_button_groups(parent_id)
    group_positions = {pos: item_ids for pos, item_ids in groups}
    
    if not items:
        # Если нет элементов, просто добавляем админ-панель и навигацию
        if parent_id is None and is_admin(user_id):
            kb.append([InlineKeyboardButton(text=BUTTON_ADMIN_PANEL, callback_data="open_admin_panel")])
    else:
        # Отображаем элементы в правильном порядке по позициям
        current_position = None
        for item in items:
            item_id = item['id']
            title = item['title']
            position = item['position']
            is_grouped = item['is_grouped']
            
            # Если это начало новой позиции
            if current_position != position:
                current_position = position
                
                if is_grouped:
                    # Отображаем группу как одну строку кнопок
                    group_items = group_positions.get(position, [])
                    if len(group_items) >= 2:
                        row = []
                        for group_item_id in group_items:
                            group_item = next((it for it in items if it['id'] == group_item_id), None)
                            if group_item:
                                # Получаем полную информацию об элементе
                                item_data = get_menu_item(group_item_id)
                                if item_data:
                                    # Формируем отображаемое название
                                    display_title = group_item['title']
                                    if has_children(group_item_id):
                                        display_title = f"{FOLDER_PREFIX}{display_title}"
                                    
                                    # Создаем кнопку
                                    if item_data[4] == "post_link" or item_data[4] == "link":
                                        # URL-кнопка для ссылок
                                        row.append(InlineKeyboardButton(text=display_title, url=item_data[3]))
                                    else:
                                        # Обычная кнопка навигации
                                        row.append(InlineKeyboardButton(text=display_title, callback_data=f"nav:{group_item_id}"))
                        
                        # Добавляем строку группы
                        if row:
                            kb.append(row)
                else:
                    # Отображаем одиночный элемент
                    item_data = get_menu_item(item_id)
                    if item_data:
                        # Формируем отображаемое название
                        display_title = title
                        if has_children(item_id):
                            display_title = f"{FOLDER_PREFIX}{display_title}"
                        
                        # Создаем кнопку
                        if item_data[4] == "post_link" or item_data[4] == "link":
                            # URL-кнопка для ссылок
                            kb.append([InlineKeyboardButton(text=display_title, url=item_data[3])])
                        else:
                            # Обычная кнопка навигации
                            kb.append([InlineKeyboardButton(text=display_title, callback_data=f"nav:{item_id}")])
        
        # Добавляем кнопку админ-панели в корневом меню для администратора
        if parent_id is None and is_admin(user_id):
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
