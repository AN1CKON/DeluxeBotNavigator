"""Обработчик стартовой команды и главного меню"""

from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from ...keyboards.keyboards import build_keyboard
from ...config.config import get_image_path
from ...database import is_new_user, register_user, update_admin_info
from ..common.utils import is_admin
from ...utils.texts import *

async def show_main_menu(message: types.Message):
    """Показывает главное меню с фото"""
    photo = FSInputFile(get_image_path("logo.JPG"))
    await message.answer_photo(
        photo, 
        reply_markup=build_keyboard(user_id=message.from_user.id)
    )

async def show_main_menu_text(message: types.Message):
    """Показывает главное меню только текстом (для редактирования)"""
    await message.answer(
        MAIN_MENU_TITLE, 
        reply_markup=build_keyboard(user_id=message.from_user.id)
    )

def register_start(dp):
    # Регистрируем функцию приветствия
    from .welcome import register_welcome
    show_welcome_message = register_welcome(dp)
    
    @dp.message(Command("start"))
    async def start(message: types.Message, state: FSMContext):
        user = message.from_user
        
        # Регистрируем пользователя
        register_user(user.id, user.username, user.first_name)
        
        # Если пользователь является администратором, обновляем его информацию
        if is_admin(user.id):
            update_admin_info(user.id, user.username, user.first_name)
        
        # Проверяем, новый ли пользователь
        if is_new_user(user.id):
            # Показываем приветствие новому пользователю
            await show_welcome_message(message, state)
        else:
            # Показываем главное меню обычному пользователю
            await show_main_menu(message)
