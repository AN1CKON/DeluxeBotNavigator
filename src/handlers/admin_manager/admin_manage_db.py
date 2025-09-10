"""Модуль для работы с базой данных и API администраторов"""

import asyncio
from typing import Dict, List, Optional, Tuple
from aiogram import Bot
from src.database import (
    add_admin as db_add_admin,
    remove_admin as db_remove_admin,
    get_all_admins as db_get_all_admins,
    get_admin_info as db_get_admin_info,
    update_admin_info as db_update_admin_info
)
from ...utils.texts import (
    ADMIN_NO_USERNAME_SHORT,
    ADMIN_NO_NAME_SHORT,
    ADMIN_NAME_FORMAT_ID,
    MSG_ADMIN_INVALID_ID,
    MSG_ADMIN_INVALID_FORMAT
)
from ..common.utils import is_admin, is_super_admin


class AdminUserManager:
    """Класс для управления пользователями-администраторами"""
    
    @staticmethod
    async def get_user_info_from_api(bot: Bot, user_id: int, chat_id: int = None) -> Dict[str, Optional[str]]:
        """
        Получает информацию о пользователе через Telegram API
        
        Args:
            bot: Экземпляр бота
            user_id: ID пользователя
            chat_id: ID чата (опционально, для get_chat_member)
            
        Returns:
            Dict с ключами 'username' и 'first_name'
        """
        username = None
        first_name = None
        
        # Метод 1: через chat_member (если пользователь был в чате и указан chat_id)
        if chat_id:
            try:
                chat_member = await bot.get_chat_member(chat_id, user_id)
                if chat_member and chat_member.user:
                    username = chat_member.user.username
                    first_name = chat_member.user.first_name
                    return {'username': username, 'first_name': first_name}
            except Exception:
                pass
        
        # Метод 2: через get_chat (прямой запрос к пользователю)
        try:
            chat = await bot.get_chat(user_id)
            if chat:
                username = chat.username
                first_name = chat.first_name
        except Exception:
            pass
        
        return {'username': username, 'first_name': first_name}
    
    @staticmethod
    async def add_admin_with_info(bot: Bot, user_id: int, added_by: int, chat_id: int = None) -> Tuple[bool, Dict[str, Optional[str]]]:
        """
        Добавляет администратора с попыткой получения информации из API
        
        Args:
            bot: Экземпляр бота
            user_id: ID нового администратора
            added_by: ID пользователя, который добавляет
            chat_id: ID чата для попытки получения информации
            
        Returns:
            Tuple: (успех операции, информация о пользователе)
        """
        # Получаем информацию о пользователе
        user_info = await AdminUserManager.get_user_info_from_api(bot, user_id, chat_id)
        
        # Добавляем администратора в базу
        success = db_add_admin(
            user_id=user_id,
            username=user_info['username'],
            first_name=user_info['first_name'],
            added_by=added_by
        )
        
        return success, user_info
    
    @staticmethod
    async def update_all_admins_info(bot: Bot, chat_id: int = None) -> int:
        """
        Обновляет информацию для всех администраторов
        
        Args:
            bot: Экземпляр бота
            chat_id: ID чата для попытки получения информации
            
        Returns:
            Количество обновленных записей
        """
        admins = db_get_all_admins()
        updated_count = 0
        
        for admin in admins:
            try:
                user_id = admin['user_id']
                
                # Получаем новую информацию
                user_info = await AdminUserManager.get_user_info_from_api(bot, user_id, chat_id)
                
                # Обновляем только если получили новую информацию
                if user_info['username'] or user_info['first_name']:
                    # Проверяем, изменилась ли информация
                    if (user_info['username'] != admin.get('username')) or (user_info['first_name'] != admin.get('first_name')):
                        db_update_admin_info(user_id, user_info['username'], user_info['first_name'])
                        updated_count += 1
                
                # Небольшая задержка между запросами
                await asyncio.sleep(0.1)
                
            except Exception:
                # Пропускаем администратора при ошибке
                continue
        
        return updated_count


class AdminDataManager:
    """Класс для работы с данными администраторов"""
    
    @staticmethod
    def get_all_admins() -> List[Dict]:
        """Возвращает список всех администраторов"""
        return db_get_all_admins()
    
    @staticmethod
    def get_admin_info(user_id: int) -> Optional[Dict]:
        """Возвращает информацию об администраторе"""
        return db_get_admin_info(user_id)
    
    @staticmethod
    def remove_admin(user_id: int) -> bool:
        """Удаляет администратора"""
        return db_remove_admin(user_id)
    
    @staticmethod
    def update_admin_info(user_id: int, username: str = None, first_name: str = None) -> bool:
        """Обновляет информацию об администраторе"""
        return db_update_admin_info(user_id, username, first_name)
    
    @staticmethod
    def get_regular_admins() -> List[Dict]:
        """Возвращает список обычных администраторов (не супер-админов)"""
        all_admins = db_get_all_admins()
        return [admin for admin in all_admins if not admin['is_super_admin']]
    
    @staticmethod
    def format_admin_name(admin_info: Dict) -> str:
        """Форматирует имя администратора для отображения"""
        if admin_info and admin_info.get('first_name'):
            return admin_info['first_name']
        else:
            return ADMIN_NAME_FORMAT_ID.format(admin_id=admin_info['user_id'])
    
    @staticmethod
    def format_admin_username(admin: Dict) -> str:
        """Форматирует username администратора для отображения"""
        if admin.get('username'):
            return f"@{admin['username']}"
        else:
            return ADMIN_NO_USERNAME_SHORT
    
    @staticmethod
    def format_admin_display_name(admin: Dict) -> str:
        """Форматирует отображаемое имя администратора"""
        return admin.get('first_name') or ADMIN_NO_NAME_SHORT


class AdminValidator:
    """Класс для валидации данных администраторов"""
    
    @staticmethod
    def validate_user_id(user_id_str: str) -> Tuple[bool, Optional[int], str]:
        """
        Валидирует ID пользователя
        
        Args:
            user_id_str: Строка с ID пользователя
            
        Returns:
            Tuple: (валидность, ID пользователя, сообщение об ошибке)
        """
        try:
            user_id = int(user_id_str.strip())
            
            # Telegram ID обычно длиннее 6 символов
            if user_id < 100000:
                return False, None, MSG_ADMIN_INVALID_ID
            
            return True, user_id, ""
            
        except ValueError:
            return False, None, MSG_ADMIN_INVALID_FORMAT
    
    @staticmethod
    def check_admin_exists(user_id: int) -> bool:
        """Проверяет, является ли пользователь уже администратором"""
        return is_admin(user_id)
    
    @staticmethod
    def check_is_super_admin(user_id: int) -> bool:
        """Проверяет, является ли пользователь супер-администратором"""
        return is_super_admin(user_id)
