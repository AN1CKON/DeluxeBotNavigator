"""Вспомогательные функции для DeluxeBotNavigator"""

import asyncio
from ..config.config import ADMIN_ID, DEFAULT_DELETE_COUNT, SUCCESS_NOTIFICATION_DELAY
from ..utils.texts import *

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id == ADMIN_ID

async def safe_delete_message(message) -> bool:
    """Безопасно удаляет сообщение. Возвращает True при успехе"""
    try:
        await message.delete()
        return True
    except Exception:
        return False

async def delete_user_messages(bot, chat_id: int, message_id: int, count: int = DEFAULT_DELETE_COUNT) -> int:
    """Удаляет несколько сообщений пользователя. Возвращает количество удаленных"""
    deleted_count = 0
    for i in range(count):
        try:
            await bot.delete_message(chat_id, message_id - i)
            deleted_count += 1
        except Exception:
            pass
    return deleted_count

async def send_notification_and_cleanup(message, text: str, delay: int = SUCCESS_NOTIFICATION_DELAY):
    """Отправляет уведомление и автоматически удаляет его через delay секунд"""
    try:
        notify = await message.answer(text)
        await asyncio.sleep(delay)
        await message.bot.delete_message(message.chat.id, notify.message_id)
    except Exception:
        pass

def get_style_display_text(content_type: str) -> str:
    """Возвращает текст стиля без эмодзи для отображения"""
    style_map = {
        "menu": BUTTON_MENU.split(' ', 1)[1],
        "text": BUTTON_TEXT.split(' ', 1)[1], 
        "attachment": BUTTON_ATTACHMENT.split(' ', 1)[1],
        "link": BUTTON_LINK.split(' ', 1)[1],
        "post_link": BUTTON_LINK.split(' ', 1)[1]
    }
    return style_map.get(content_type, content_type)

def validate_url(url: str) -> bool:
    """Проверяет корректность URL"""
    if not url:
        return False
    return url.startswith("http://") or url.startswith("https://")

def format_menu_item_display(title: str, content_type: str, has_children_flag: bool = False) -> str:
    """Форматирует отображение элемента меню"""
    prefix = ""
    if content_type == "menu" or has_children_flag:
        prefix = FOLDER_PREFIX
    elif content_type == "text":
        prefix = TEXT_PREFIX
    elif content_type in ["link", "post_link"]:
        prefix = LINK_PREFIX
    
    return f"{prefix}{title}"
