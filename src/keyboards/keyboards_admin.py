"""Клавиатуры для админ-панели DeluxeBotNavigator"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..database import get_menu_items, get_menu_item, has_children
from ..utils.texts import *

def get_style_display_text(content_type: str) -> str:
    """Возвращает текст стиля без эмодзи для отображения"""
    style_map = {
        "menu": BUTTON_MENU.split(' ', 1)[1],
        "text": BUTTON_TEXT.split(' ', 1)[1], 
        "attachment": BUTTON_ATTACHMENT.split(' ', 1)[1],
        "link": BUTTON_LINK.split(' ', 1)[1],
        "post_link": BUTTON_LINK.split(' ', 1)[1],
        "stats": "Статистика"
    }
    return style_map.get(content_type, content_type)

# ========== АДМИНСКИЕ КЛАВИАТУРЫ ==========

def admin_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура админ-панели"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BUTTON_ADD, callback_data="admin_add"),
             InlineKeyboardButton(text=BUTTON_EDIT, callback_data="admin_edit")],
            [InlineKeyboardButton(text=BUTTON_DELETE, callback_data="admin_delete"),
             InlineKeyboardButton(text=BUTTON_ORDER_MODE, callback_data="admin_move_mode")],
            [InlineKeyboardButton(text=BUTTON_ADMIN_MANAGER, callback_data="manage_admins"),
             InlineKeyboardButton(text="📊 Статистика", callback_data="manage_stats")],
            [InlineKeyboardButton(text=BUTTON_CLEAR, callback_data="admin_clear")],
            [InlineKeyboardButton(text=BUTTON_CLOSE, callback_data="admin_close")],
        ]
    )

def cancel_button() -> InlineKeyboardMarkup:
    """Простая кнопка отмены для админских операций"""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="admin_cancel")]]
    )

def parent_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора родительского меню для добавления"""
    buttons = []
    for item_id, title in get_menu_items():
        menu_item = get_menu_item(item_id)
        if menu_item:
            style = get_style_display_text(menu_item[4])
            prefix = FOLDER_PREFIX if has_children(item_id) else ""
            display_title = f"{prefix}{title} [{style}]"
        else:
            display_title = title
        buttons.append([InlineKeyboardButton(text=display_title, callback_data=f"set_parent:{item_id}")])
    
    buttons.extend([
        [InlineKeyboardButton(text=BUTTON_ADD_TO_ROOT, callback_data="set_parent:0")],
        [InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="admin_cancel")]
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def delete_menu_keyboard(parent_id=None) -> InlineKeyboardMarkup:
    """Клавиатура для выбора элемента для удаления"""
    buttons = []
    for item_id, title in get_menu_items(parent_id):
        menu_item = get_menu_item(item_id)
        style = get_style_display_text(menu_item[4]) if menu_item else ""
        prefix = FOLDER_PREFIX if has_children(item_id) else ""
        display_title = f"{prefix}{title} [{style}]" if style else title
        buttons.append([InlineKeyboardButton(text=display_title, callback_data=f"delete_parent:{item_id}")])
    
    if parent_id is not None:
        buttons.append([InlineKeyboardButton(text=BUTTON_DELETE_SECTION, callback_data=f"delete_section:{parent_id}")])
    
    buttons.append([
        InlineKeyboardButton(text=BUTTON_BACK, callback_data="admin_panel"),
        InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="admin_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def edit_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора элемента для редактирования"""
    buttons = []
    for item_id, title in get_menu_items():
        menu_item = get_menu_item(item_id)
        if menu_item:
            style = get_style_display_text(menu_item[4])
            display_title = f"{FOLDER_PREFIX if has_children(item_id) else ''}{title} [{style}]"
        else:
            display_title = title
        buttons.append([InlineKeyboardButton(text=display_title, callback_data=f"edit_parent:{item_id}")])
    
    buttons.append([
        InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="admin_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def edit_children_keyboard(parent_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора дочернего элемента для редактирования"""
    buttons = []
    for item_id, title in get_menu_items(parent_id):
        menu_item = get_menu_item(item_id)
        if menu_item:
            style = get_style_display_text(menu_item[4])
            display_title = f"{title} [{style}]"
        else:
            display_title = title
        buttons.append([InlineKeyboardButton(text=display_title, callback_data=f"edit_item:{item_id}")])
    
    buttons.extend([
        [InlineKeyboardButton(text=BUTTON_EDIT_CURRENT, callback_data=f"edit_item:{parent_id}")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="admin_edit"),
         InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="admin_cancel")]
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_keyboard(confirm_callback: str, back_callback: str, confirm_text: str = BUTTON_CONFIRM_DELETE) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=confirm_text, callback_data=confirm_callback),
         InlineKeyboardButton(text=BUTTON_BACK, callback_data=back_callback)]
    ])

def style_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора стиля кнопки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_MENU, callback_data="ctype:menu"),
         InlineKeyboardButton(text=BUTTON_TEXT, callback_data="ctype:text")],
        [InlineKeyboardButton(text=BUTTON_ATTACHMENT, callback_data="ctype:attachment"),
         InlineKeyboardButton(text=BUTTON_LINK, callback_data="ctype:link")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="ctype:stats")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="back_to_title"), 
         InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="admin_cancel")]
    ])

def edit_style_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора стиля для редактирования"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_MENU, callback_data="edit_ctype:menu"),
         InlineKeyboardButton(text=BUTTON_TEXT, callback_data="edit_ctype:text")],
        [InlineKeyboardButton(text=BUTTON_ATTACHMENT, callback_data="edit_ctype:attachment"),
         InlineKeyboardButton(text=BUTTON_LINK, callback_data="edit_ctype:link")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="edit_ctype:stats")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="back_to_edit_title"), 
         InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="admin_cancel")]
    ])

def back_cancel_keyboard(back_callback: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками 'Назад' и 'Отмена'"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data=back_callback), 
         InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="admin_cancel")]
    ])

def image_choice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора действия с изображением при добавлении"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_SKIP_IMAGE, callback_data="skip_image")],
        [InlineKeyboardButton(text=BUTTON_BACK, callback_data="back_to_style"), 
         InlineKeyboardButton(text=BUTTON_CANCEL, callback_data="admin_cancel")]
    ])
