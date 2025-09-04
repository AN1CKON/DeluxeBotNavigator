"""Обработчик отмены админских операций"""

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from .utils import safe_delete_message
from ..keyboards.keyboards_admin import admin_keyboard
from ..config.config import get_image_path
from ..utils.texts import *

def register_admin_cancel(dp):
    """Централизованный обработчик отмены админ-действий"""
    @dp.callback_query(F.data == "admin_cancel")
    async def cancel_admin(callback: types.CallbackQuery, state: FSMContext = None):
        """Отмена любого админского действия и возврат в панель"""
        await safe_delete_message(callback.message)
        await callback.answer()
        
        # Очищаем состояние если оно есть
        if state:
            await state.clear()
        
        # Возвращаем админ-панель
        photo = FSInputFile(get_image_path("admin.JPG"))
        await callback.message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())
