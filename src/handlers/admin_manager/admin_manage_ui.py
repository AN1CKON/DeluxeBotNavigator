"""Модуль UI компонентов для управления администраторами"""

import asyncio
from typing import List, Dict
from aiogram import types
from src.utils.texts import (
    ADMIN_MANAGE_TITLE,
    ADMIN_DETAILED_LIST_TITLE,
    BUTTON_ADD_ADMIN,
    BUTTON_REMOVE_ADMIN,
    BUTTON_LIST_ADMINS,
    BUTTON_UPDATE_ADMIN_INFO,
    BUTTON_MANAGE_SUPER_ADMINS,
    BUTTON_ADMIN_OK,
    BUTTON_BACK,
    BUTTON_CANCEL,
    BUTTON_CONFIRM_UPDATE,
    ADMIN_STATUS_SUPER,
    ADMIN_STATUS_REGULAR,
    ADMIN_STATUS_SUPER_DETAILED,
    ADMIN_STATUS_REGULAR_DETAILED,
    MSG_ADMIN_NO_ADMINS_FOUND,
    ADMIN_NO_USERNAME,
    ADMIN_NO_NAME,
    ADMIN_LIST_HEADER,
    ADMIN_DEFAULT_COUNTDOWN_TEXT,
    ADMIN_DATE_UNKNOWN,
    MSG_ADMIN_AUTO_INFO_FOUND,
    MSG_ADMIN_AUTO_INFO_NAME,
    MSG_ADMIN_AUTO_INFO_USERNAME,
    MSG_ADMIN_AUTO_INFO_NOT_FOUND
)
from .admin_manage_db import AdminDataManager
from ..common.utils import safe_delete_message


class AdminMessageHandler:
    """Класс для работы с сообщениями администратора"""
    
    @staticmethod
    async def send_countdown_message(message: types.Message, text: str, 
                                   countdown_seconds: int = 3, action_text: str = ADMIN_DEFAULT_COUNTDOWN_TEXT):
        """Универсальная функция для отправки сообщений с таймером"""
        try:
            await safe_delete_message(message)
            
            sent_message = await message.answer(f"{text} ({countdown_seconds})")
            
            for i in range(countdown_seconds - 1, 0, -1):
                await asyncio.sleep(1)
                try:
                    await sent_message.edit_text(f"{text} ({i})")
                except Exception:
                    pass
            
            await asyncio.sleep(1)
            await safe_delete_message(sent_message)
            
        except Exception:
            await message.answer(text)
    
    @staticmethod
    async def clear_chat_messages(bot, chat_id: int, start_message_id: int, count: int = 10):
        """Удаляет несколько сообщений из чата"""
        deleted_count = 0
        for i in range(count):
            try:
                await bot.delete_message(chat_id, start_message_id - i)
                deleted_count += 1
                # Небольшая задержка между удалениями для избежания rate limit
                await asyncio.sleep(0.1)
            except Exception:
                pass
        return deleted_count


class AdminMenuBuilder:
    """Класс для построения меню администратора"""
    
    @staticmethod
    def build_admin_list_text(admins: List[Dict]) -> str:
        """Создает текст списка администраторов"""
        if not admins:
            return f"{ADMIN_MANAGE_TITLE}{MSG_ADMIN_NO_ADMINS_FOUND}"
        
        text = f"{ADMIN_MANAGE_TITLE}{ADMIN_LIST_HEADER}"
        for admin in admins:
            status = ADMIN_STATUS_SUPER if admin['is_super_admin'] else ADMIN_STATUS_REGULAR
            username = AdminDataManager.format_admin_username(admin)
            name = AdminDataManager.format_admin_display_name(admin)
            text += f"• {status}: {name} ({username})\n"
        return text
    
    @staticmethod
    def build_detailed_admin_list_text(admins: List[Dict]) -> str:
        """Создает подробный текст списка администраторов"""
        if not admins:
            return MSG_ADMIN_NO_ADMINS_FOUND
        
        text = ADMIN_DETAILED_LIST_TITLE
        for i, admin in enumerate(admins, 1):
            status = ADMIN_STATUS_SUPER_DETAILED if admin['is_super_admin'] else ADMIN_STATUS_REGULAR_DETAILED
            username = f"@{admin['username']}" if admin['username'] else ADMIN_NO_USERNAME
            name = admin['first_name'] or ADMIN_NO_NAME
            added_date = admin['added_at'][:10] if admin['added_at'] else ADMIN_DATE_UNKNOWN
            
            text += f"{i}. {status}\n"
            text += f"👤 Имя: {name}\n"
            text += f"🆔 Username: {username}\n"
            text += f"🔢 ID: <code>{admin['user_id']}</code>\n"
            text += f"📅 Добавлен: {added_date}\n"
            
            if admin['added_by'] and admin['added_by'] != admin['user_id']:
                text += f"➕ Добавил: <code>{admin['added_by']}</code>\n"
            text += "\n"
        
        return text
    
    @staticmethod
    def build_admin_removal_list(admins: List[Dict]) -> str:
        """Создает список администраторов для удаления"""
        admin_list = ""
        for admin in admins:
            username = AdminDataManager.format_admin_username(admin)
            name = AdminDataManager.format_admin_display_name(admin)
            admin_list += f"• {name} ({username}) - ID: <code>{admin['user_id']}</code>\n"
        return admin_list
    
    @staticmethod
    def build_success_message_with_info(base_message: str, user_info: Dict) -> str:
        """Создает сообщение об успехе с информацией о пользователе"""
        message = base_message
        
        if user_info.get('username') or user_info.get('first_name'):
            message += MSG_ADMIN_AUTO_INFO_FOUND
            if user_info.get('first_name'):
                message += MSG_ADMIN_AUTO_INFO_NAME.format(name=user_info['first_name'])
            if user_info.get('username'):
                message += MSG_ADMIN_AUTO_INFO_USERNAME.format(username=user_info['username'])
        else:
            message += MSG_ADMIN_AUTO_INFO_NOT_FOUND
        
        return message


class AdminKeyboardBuilder:
    """Класс для построения клавиатур администратора"""
    
    @staticmethod
    def build_main_keyboard() -> types.InlineKeyboardMarkup:
        """Создает основную клавиатуру управления администраторами"""
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text=BUTTON_ADD_ADMIN, callback_data="add_admin"),
                types.InlineKeyboardButton(text=BUTTON_REMOVE_ADMIN, callback_data="remove_admin")
            ],
            [
                types.InlineKeyboardButton(text=BUTTON_LIST_ADMINS, callback_data="list_admins"),
                types.InlineKeyboardButton(text=BUTTON_UPDATE_ADMIN_INFO, callback_data="update_admin_info")
            ],
            [
                types.InlineKeyboardButton(text=BUTTON_MANAGE_SUPER_ADMINS, callback_data="manage_super_admins")
            ],
            [
                types.InlineKeyboardButton(text=BUTTON_BACK, callback_data="admin_panel")
            ]
        ])
    
    @staticmethod
    def build_back_keyboard(callback_data: str = "manage_admins") -> types.InlineKeyboardMarkup:
        """Создает клавиатуру с кнопкой назад"""
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=BUTTON_BACK, callback_data=callback_data)]
        ])
    
    @staticmethod
    def build_cancel_keyboard(callback_data: str = "manage_admins") -> types.InlineKeyboardMarkup:
        """Создает клавиатуру с кнопкой отмены"""
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=BUTTON_CANCEL, callback_data=callback_data)]
        ])
    
    @staticmethod
    def build_success_keyboard(admin_id: int) -> types.InlineKeyboardMarkup:
        """Создает клавиатуру для успешного добавления администратора"""
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=BUTTON_ADMIN_OK, callback_data=f"admin_added_ok:{admin_id}")]
        ])
    
    @staticmethod
    def build_confirmation_keyboard(confirm_callback: str, cancel_callback: str = "manage_admins") -> types.InlineKeyboardMarkup:
        """Создает клавиатуру подтверждения действия"""
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text=BUTTON_CONFIRM_UPDATE, callback_data=confirm_callback),
                types.InlineKeyboardButton(text=BUTTON_CANCEL, callback_data=cancel_callback)
            ]
        ])


class AdminUIHelper:
    """Вспомогательный класс для UI операций"""
    
    @staticmethod
    async def show_admin_manage_menu(target):
        """Универсальная функция показа меню управления администраторами"""
        admins = AdminDataManager.get_all_admins()
        text = AdminMenuBuilder.build_admin_list_text(admins)
        keyboard = AdminKeyboardBuilder.build_main_keyboard()
        
        await target.answer(text, reply_markup=keyboard)
    
    @staticmethod
    async def show_progress_message(message: types.Message, text: str, duration: int = 3) -> types.Message:
        """Показывает прогресс-сообщение на указанное время"""
        progress_msg = await message.answer(text)
        return progress_msg
    
    @staticmethod
    async def update_progress_message(message: types.Message, new_text: str):
        """Обновляет прогресс-сообщение"""
        try:
            await message.edit_text(new_text)
        except Exception:
            pass  # Игнорируем ошибки редактирования
