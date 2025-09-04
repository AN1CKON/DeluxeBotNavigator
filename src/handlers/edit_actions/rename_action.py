"""Обработчик переименования кнопки"""

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from ...database.db import update_menu_item, get_menu_item
from ...models.states import MenuState
from ..utils import safe_delete_message, delete_user_messages, send_notification_and_cleanup
from ...utils.texts import *

def register_rename_action(dp):
    """Регистрация обработчиков для переименования кнопки"""
    
    @dp.callback_query(F.data.startswith("edit_action_rename:"))
    async def handle_rename_action(callback: types.CallbackQuery, state: FSMContext):
        """Обработка действия переименования кнопки"""
        item_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        
        # Сохраняем ID элемента в состоянии
        await state.update_data(rename_item_id=item_id)
        await state.set_state(MenuState.waiting_for_rename_title)
        
        await callback.message.answer(
            MSG_ENTER_TITLE,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=BUTTON_BACK, callback_data=f"back_to_edit_menu:{item_id}")]
            ])
        )
    
    @dp.message(MenuState.waiting_for_rename_title)
    async def handle_rename_title_input(message: types.Message, state: FSMContext):
        """Обработка ввода нового названия"""
        if not message.text:
            return await message.answer(MSG_ERROR_TEXT_ONLY)
        
        data = await state.get_data()
        item_id = data.get("rename_item_id")
        
        if not item_id:
            await state.clear()
            return await message.answer("❌ Ошибка: элемент не найден")
        
        # Получаем текущие данные элемента
        menu_item = get_menu_item(item_id)
        if not menu_item:
            await state.clear()
            return await message.answer(MSG_ERROR_ITEM_NOT_FOUND)
        
        # Обновляем только название, оставляя остальные поля без изменений
        success = update_menu_item(
            item_id,
            title=message.text.strip(),
            content=menu_item[3],  # content
            content_type=menu_item[4],  # content_type
            parent_id=menu_item[1]  # parent_id
        )
        
        # Удаляем пользовательское сообщение
        await delete_user_messages(message.bot, message.chat.id, message.message_id)
        
        if success:
            # Уведомляем об успехе и возвращаем в меню редактирования кнопки
            await send_notification_and_cleanup(message, MSG_ITEM_UPDATED)
            # Показываем меню редактирования кнопки
            from . import edit_menu
            await edit_menu.show_edit_button_menu(message, item_id, state)
        else:
            await message.answer("❌ Ошибка при переименовании элемента")
        
        await state.clear()
    
    @dp.callback_query(F.data.startswith("back_to_edit_menu:"))
    async def handle_back_to_edit_menu(callback: types.CallbackQuery, state: FSMContext):
        """Возврат к меню редактирования кнопки"""
        item_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        await state.clear()
        
        # Показываем меню редактирования кнопки
        from . import edit_menu
        await edit_menu.show_edit_button_menu(callback.message, item_id, state)
