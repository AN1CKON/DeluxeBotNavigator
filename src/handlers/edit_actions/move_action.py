"""Обработчик перемещения кнопки"""

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from ..utils import safe_delete_message

def register_move_action(dp):
    """Регистрация обработчиков для перемещения кнопки"""
    
    @dp.callback_query(F.data.startswith("edit_action_move:"))
    async def handle_move_action(callback: types.CallbackQuery, state: FSMContext):
        """Обработка действия перемещения кнопки"""
        await safe_delete_message(callback.message)
        await callback.answer("⚠️ Данная функция ещё в разработке", show_alert=True)
        
        # Возвращаемся к меню редактирования кнопки
        item_id = int(callback.data.split(":")[1])
        from . import edit_menu
        await edit_menu.show_edit_button_menu(callback.message, item_id, state)
