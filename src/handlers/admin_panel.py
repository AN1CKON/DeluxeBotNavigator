"""Обработчик админ-панели"""

from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from .utils import is_admin, safe_delete_message
from ..keyboards.keyboards_admin import admin_keyboard
from ..keyboards.keyboards import build_keyboard
from ..config.config import get_image_path
from ..utils.texts import *

def register_admin_panel(dp, bot):
    from .start import show_main_menu_for_callback

    @dp.message(Command("admin"))
    async def admin_panel_command(message: types.Message):
        """Обработчик команды /admin для входа в админ-панель"""
        if not is_admin(message.from_user.id):
            return await message.answer(NO_ACCESS_MESSAGE)
        
        photo = FSInputFile(get_image_path("admin.JPG"))
        await message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())

    @dp.callback_query(F.data == "open_admin_panel")
    async def open_admin_panel_callback(callback: types.CallbackQuery):
        """Обработчик кнопки админ-панели в главном меню"""
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
        
        await safe_delete_message(callback.message)
        photo = FSInputFile(get_image_path("admin.JPG"))
        await callback.message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())

    @dp.callback_query(F.data == "admin_close")
    async def admin_close_callback(callback: types.CallbackQuery):
        """Обработчик закрытия админ-панели"""
        await safe_delete_message(callback.message)
        await callback.answer()
        # Используем специальную функцию для callback'ов
        await show_main_menu_for_callback(callback)

    @dp.callback_query(F.data == "admin_panel") 
    async def back_to_admin_panel(callback: types.CallbackQuery):
        """Возврат к главной админ-панели"""
        await safe_delete_message(callback.message)
        photo = FSInputFile(get_image_path("admin.JPG"))
        await callback.message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())
