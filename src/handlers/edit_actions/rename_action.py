"""Обработчик переименования кнопки"""

import asyncio
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from ...database import update_menu_item, get_menu_item
from ...models.states import MenuState
from ..common.utils import safe_delete_message, delete_user_messages, send_notification_and_cleanup
from ...utils.texts import *
from . import edit_menu

def register_rename_action(dp):
    """Регистрация обработчиков для переименования кнопки"""
    
    @dp.callback_query(F.data.startswith("edit_action_rename:"))
    async def handle_rename_action(callback: types.CallbackQuery, state: FSMContext):
        """Обработка действия переименования кнопки"""
        item_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        
        # Получаем текущие данные элемента для показа информации
        menu_item = get_menu_item(item_id)
        if not menu_item:
            await callback.answer(MSG_ERROR_ITEM_NOT_FOUND, show_alert=True)
            return
            
        current_title = menu_item[2]  # текущее название
        
        # Сохраняем ID элемента в состоянии
        await state.update_data(rename_item_id=item_id)
        await state.set_state(MenuState.waiting_for_rename_title)
        
        # Создаем информативное сообщение с текущим названием
        message_text = MSG_RENAME_CURRENT_TITLE.format(
            current_title=current_title,
            enter_title_msg=MSG_ENTER_TITLE
        )
        
        await callback.message.answer(
            message_text,
            parse_mode="HTML",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=BUTTON_CANCEL, callback_data=f"back_to_edit_menu:{item_id}")]
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
            return await message.answer(MSG_ERROR_RENAME_ITEM_NOT_FOUND)
        
        # Получаем текущие данные элемента
        menu_item = get_menu_item(item_id)
        if not menu_item:
            await state.clear()
            return await message.answer(MSG_ERROR_ITEM_NOT_FOUND)
        
        old_title = menu_item[2]  # старое название
        new_title = message.text.strip()  # новое название
        
        # Проверяем, не пытается ли пользователь установить то же название
        if old_title == new_title:
            await delete_user_messages(message.bot, message.chat.id, message.message_id)
            await message.answer(
                MSG_ERROR_RENAME_SAME_NAME.format(title=new_title),
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=BUTTON_CANCEL, callback_data=f"back_to_edit_menu:{item_id}")]
                ])
            )
            return
        
        # Обновляем только название, оставляя остальные поля без изменений
        success = update_menu_item(
            item_id,
            title=new_title,
            content=menu_item[3],  # content
            content_type=menu_item[4],  # content_type
            parent_id=menu_item[1]  # parent_id
        )
        
        # Удаляем пользовательское сообщение
        await delete_user_messages(message.bot, message.chat.id, message.message_id)
        
        if success:
            # Показываем информацию об изменении с красивым форматированием
            change_info = MSG_RENAME_SUCCESS.format(
                old_title=old_title,
                new_title=new_title
            )
            
            # Отправляем уведомление с HTML форматированием
            try:
                notify = await message.answer(change_info, parse_mode="HTML")
                await asyncio.sleep(3)  # показываем 3 секунды
                await message.bot.delete_message(message.chat.id, notify.message_id)
            except Exception:
                pass
            
            # Показываем меню редактирования кнопки
            await edit_menu.show_edit_button_menu(message, item_id, state)
        else:
            await message.answer(MSG_ERROR_RENAME_FAILED)
        
        await state.clear()
    
    @dp.callback_query(F.data.startswith("back_to_edit_menu:"))
    async def handle_back_to_edit_menu(callback: types.CallbackQuery, state: FSMContext):
        """Возврат к меню редактирования кнопки"""
        item_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        await state.clear()
        
        # Показываем меню редактирования кнопки
        await edit_menu.show_edit_button_menu(callback.message, item_id, state)
