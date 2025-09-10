"""Обработчик изменения стиля кнопки"""

import asyncio
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from src.database import update_menu_item, get_menu_item
from src.models import MenuState
from src.handlers.common.utils import safe_delete_message, delete_user_messages, send_notification_and_cleanup, validate_url
from src.keyboards.keyboards_admin import edit_style_keyboard
from src.utils.texts import *
from . import edit_menu

async def cleanup_invalid_url_messages(user_message, error_message, delay: int):
    """Удаляет сообщение пользователя и уведомление об ошибке с динамическим таймером"""
    try:
        # Показываем обратный отсчёт
        for remaining in range(delay, 0, -1):
            countdown_text = f"❌ Некорректная ссылка! Введите корректный URL: ({remaining})"
            await error_message.edit_text(countdown_text)
            await asyncio.sleep(1)
        
        # Удаляем сообщения
        await user_message.delete()
        await error_message.delete()
    except Exception:
        # Если произошла ошибка, просто удаляем сообщения без таймера
        try:
            await user_message.delete()
        except:
            pass
        try:
            await error_message.delete()
        except:
            pass

def register_style_action(dp):
    """Регистрация обработчиков для изменения стиля кнопки"""
    
    @dp.callback_query(F.data.startswith("edit_action_style:"))
    async def handle_style_action(callback: types.CallbackQuery, state: FSMContext):
        """Обработка действия изменения стиля кнопки"""
        item_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        
        # Сохраняем ID элемента в состоянии
        await state.update_data(style_item_id=item_id)
        await state.set_state(MenuState.waiting_for_style_type)
        
        await callback.message.answer(
            MSG_CHOOSE_STYLE,
            reply_markup=edit_style_keyboard_with_back(item_id),
            parse_mode="HTML"
        )
    
    @dp.callback_query(F.data.startswith("edit_style_ctype:"))
    async def handle_style_content_type(callback: types.CallbackQuery, state: FSMContext):
        """Обработка выбора нового стиля"""
        await safe_delete_message(callback.message)
        content_type = callback.data.replace("edit_style_ctype:", "")
        data = await state.get_data()
        item_id = data.get("style_item_id")
        
        if not item_id:
            await state.clear()
            return await callback.answer("❌ Ошибка: элемент не найден", show_alert=True)
        
        # Получаем текущие данные элемента
        menu_item = get_menu_item(item_id)
        if not menu_item:
            await state.clear()
            return await callback.answer(MSG_ERROR_ITEM_NOT_FOUND, show_alert=True)
        
        await state.update_data(content_type=content_type)
        
        if content_type == "menu":
            # Обновляем элемент как меню (контент = None)
            success = update_menu_item(
                item_id,
                title=menu_item[2],  # title
                content=None,
                content_type="menu",
                parent_id=menu_item[1]  # parent_id
            )
            
            if success:
                await notify_and_return_to_edit_menu(callback.message, item_id, state)
            else:
                await callback.message.answer("❌ Ошибка при изменении стиля")
            
            await state.clear()
            return
            
        if content_type == "attachment":
            # Функционал в разработке
            kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=BUTTON_BACK, callback_data=f"edit_action_style:{item_id}")]
            ])
            await callback.message.answer(MSG_FEATURE_IN_DEVELOPMENT, reply_markup=kb, parse_mode="HTML")
            return
            
        if content_type == "review":
            # Для отзывов обновляем тип контента без изменения содержимого
            success = update_menu_item(
                item_id,
                title=menu_item[2],  # title
                content=None,  # content
                content_type="review",
                parent_id=menu_item[1]  # parent_id
            )
            
            if success:
                await notify_and_return_to_edit_menu(callback.message, item_id, state)
            else:
                await callback.message.answer("❌ Ошибка при изменении стиля")
            
            await state.clear()
            return
            
        # Запрашиваем новый контент для text, link, post_link
        await state.set_state(MenuState.waiting_for_style_content)
        msg = {
            "text": MSG_ENTER_CONTENT_TEXT,
            "link": MSG_ENTER_CONTENT_LINK,
            "post_link": MSG_ENTER_CONTENT_LINK
        }.get(content_type, MSG_ENTER_CONTENT_TEXT)
        
        await callback.message.answer(
            msg,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=BUTTON_BACK, callback_data=f"edit_action_style:{item_id}")]
            ])
        )
    
    @dp.message(MenuState.waiting_for_style_content)
    async def handle_style_content_input(message: types.Message, state: FSMContext):
        """Обработка ввода нового контента для стиля"""
        if not message.text:
            return await message.answer(MSG_ERROR_TEXT_ONLY)
        
        data = await state.get_data()
        item_id = data.get("style_item_id")
        content_type = data.get("content_type")
        content = message.text.strip()
        
        if not item_id or not content_type:
            await state.clear()
            return await message.answer("❌ Ошибка: данные не найдены")
        
        # Валидация контента
        if content_type in ["link", "post_link"] and not validate_url(content):
            # Отправляем временное уведомление об ошибке
            error_msg = await message.answer(MSG_INVALID_URL)
            # Создаём асинхронную задачу для удаления сообщений через 3 секунды
            asyncio.create_task(cleanup_invalid_url_messages(message, error_msg, 3))
            return
        
        # Получаем текущие данные элемента
        menu_item = get_menu_item(item_id)
        if not menu_item:
            await state.clear()
            return await message.answer(MSG_ERROR_ITEM_NOT_FOUND)
        
        # Удаляем пользовательское сообщение
        await delete_user_messages(message.bot, message.chat.id, message.message_id)
        
        # Обновляем элемент меню
        success = update_menu_item(
            item_id,
            title=menu_item[2],  # title
            content=content,
            content_type=content_type,
            parent_id=menu_item[1]  # parent_id
        )
        
        if success:
            await notify_and_return_to_edit_menu(message, item_id, state)
        else:
            await message.answer("❌ Ошибка при изменении стиля")
        
        await state.clear()

def edit_style_keyboard_with_back(item_id: int) -> types.InlineKeyboardMarkup:
    """Клавиатура выбора стиля с кнопкой возврата к меню редактирования"""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        # Первая строка - 2 кнопки
        [
            types.InlineKeyboardButton(text=BUTTON_MENU, callback_data="edit_style_ctype:menu"),
            types.InlineKeyboardButton(text=BUTTON_TEXT, callback_data="edit_style_ctype:text")
        ],
        # Вторая строка - 2 кнопки  
        [
            types.InlineKeyboardButton(text=BUTTON_LINK, callback_data="edit_style_ctype:link"),
            types.InlineKeyboardButton(text=BUTTON_ATTACHMENT, callback_data="edit_style_ctype:attachment")
        ],
        # Третья строка - статистика и отзыв
        [
            types.InlineKeyboardButton(text="📊 Статистика", callback_data="edit_style_ctype:stats"),
            types.InlineKeyboardButton(text=BUTTON_REVIEW, callback_data="edit_style_ctype:review")
        ],
        # Четвертая строка - кнопка назад
        [types.InlineKeyboardButton(text=BUTTON_BACK, callback_data=f"back_to_edit_menu:{item_id}")]
    ])

async def notify_and_return_to_edit_menu(message, item_id, state):
    """Уведомляет об успехе и возвращает в меню редактирования кнопки"""
    await send_notification_and_cleanup(message, MSG_ITEM_UPDATED)
    # Показываем меню редактирования кнопки
    await edit_menu.show_edit_button_menu(message, item_id, state)
