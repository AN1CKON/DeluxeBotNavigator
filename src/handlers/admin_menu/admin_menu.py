"""Обработчик админ-меню"""

from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.handlers.common.utils import is_admin, safe_delete_message, show_main_menu_for_callback
from src.keyboards.keyboards_admin import admin_keyboard, admin_settings_keyboard
from src.keyboards.keyboards import build_keyboard
from src.config.config import get_image_path
from src.database import update_admin_info
from src.utils.texts import *
from src.models import AdminStates
from src.handlers.admin_menu.admin_stats import show_stats_management
from src.handlers.user_interface.review_ui.review_stats import show_reviews_management

def register_admin_menu_handlers(dp, bot):
    """Регистрация основных обработчиков админ-меню"""

    @dp.message(Command("admin"))
    async def admin_panel_command(message: types.Message):
        """Обработчик команды /admin для входа в админ-панель"""
        if not is_admin(message.from_user.id):
            return await message.answer(NO_ACCESS_MESSAGE)
        
        # Обновляем информацию об администраторе
        update_admin_info(message.from_user.id, message.from_user.username, message.from_user.first_name)
        
        photo = FSInputFile(get_image_path("admin.JPG"))
        await message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())

    @dp.callback_query(F.data == "open_admin_panel")
    async def open_admin_panel_callback(callback: types.CallbackQuery):
        """Обработчик кнопки админ-панели в главном меню"""
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
        
        # Обновляем информацию об администраторе
        update_admin_info(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
        
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

    @dp.callback_query(F.data == "manage_stats")
    async def manage_stats_callback(callback: types.CallbackQuery):
        """Обработчик управления статистикой плагинов"""
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
        
        await safe_delete_message(callback.message)
        await show_stats_management(callback.message)

    @dp.callback_query(F.data == "manage_reviews")
    async def manage_reviews_callback(callback: types.CallbackQuery):
        """Обработчик управления отзывами"""
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)

        await safe_delete_message(callback.message)
        await show_reviews_management(callback.message)

    @dp.callback_query(F.data == "admin_settings")
    async def admin_settings_callback(callback: types.CallbackQuery):
        """Обработчик кнопки настроек админ-панели"""
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
        
        await safe_delete_message(callback.message)
        await callback.message.answer("⚙️ Настройки", reply_markup=admin_settings_keyboard())

    @dp.callback_query(F.data == "back_to_admin")
    async def back_to_admin_callback(callback: types.CallbackQuery):
        """Обработчик возврата в админ-панель"""
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)
        
        await safe_delete_message(callback.message)
        photo = FSInputFile(get_image_path("admin.JPG"))
        await callback.message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())
