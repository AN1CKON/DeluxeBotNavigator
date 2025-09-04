"""Обработчик редактирования пунктов меню"""

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from ..database.db import get_menu_item, has_children
from ..models.states import MenuState
from .utils import safe_delete_message
from ..keyboards.keyboards_admin import edit_menu_keyboard, edit_children_keyboard
from ..utils.texts import *
from .edit_actions.edit_menu import show_edit_button_menu
from .edit_actions import register_edit_actions

def register_admin_edit(dp):
    """Регистрация обработчиков редактирования"""
    
    # Регистрируем основные обработчики редактирования
    @dp.callback_query(F.data == "admin_edit")
    async def admin_edit_start(callback: types.CallbackQuery, state: FSMContext):
        """Начало процесса редактирования"""
        await safe_delete_message(callback.message)
        await state.clear()
        await state.set_state(MenuState.waiting_for_edit_item)
        await callback.message.answer(MSG_CHOOSE_EDIT_ITEM, reply_markup=edit_menu_keyboard())

    @dp.callback_query(F.data.startswith("edit_parent:"))
    async def edit_parent_select(callback: types.CallbackQuery, state: FSMContext):
        """Выбор родительского элемента для редактирования"""
        parent_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        
        if has_children(parent_id):
            # Если есть дочерние элементы, показываем их
            await state.set_state(MenuState.waiting_for_edit_item)
            await callback.message.answer(MSG_CHOOSE_EDIT_ITEM, reply_markup=edit_children_keyboard(parent_id))
        else:
            # Открываем меню редактирования для этого элемента
            await state.clear()
            await show_edit_button_menu(callback.message, parent_id, state)

    @dp.callback_query(F.data.startswith("edit_item:"))
    async def edit_item_select(callback: types.CallbackQuery, state: FSMContext):
        """Выбор конкретного элемента для редактирования"""
        item_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        
        menu_item = get_menu_item(item_id)
        if not menu_item:
            return await callback.answer(MSG_ERROR_ITEM_NOT_FOUND, show_alert=True)
        
        # Открываем новое меню редактирования кнопки
        await state.clear()
        await show_edit_button_menu(callback.message, item_id, state)
    
    # Регистрируем обработчики действий редактирования
    register_edit_actions(dp)
