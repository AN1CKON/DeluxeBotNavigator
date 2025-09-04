"""Обработчик навигации по меню"""

import os
from aiogram import types, F
from aiogram.types import FSInputFile
from ..keyboards.keyboards import build_keyboard, close_text_keyboard
from ..database.db import get_menu_item
from .utils import safe_delete_message, format_menu_item_display
from ..utils.texts import *
from ..config.config import MEDIA_PATH

def register_navigation(dp):

    @dp.callback_query(F.data.startswith("nav:"))
    async def navigate(callback: types.CallbackQuery):
        """Обработчик навигации по меню"""
        data = callback.data.replace("nav:", "")
        
        if data == "root":
            # Возвращаемся к главному меню - показываем logo.JPG
            await safe_delete_message(callback.message)
            from .start import show_main_menu_for_callback
            await show_main_menu_for_callback(callback)
            return
            
        item_id = int(data)
        item = get_menu_item(item_id)
        
        if not item:
            return await callback.answer(MSG_ERROR_ITEM_NOT_FOUND, show_alert=True)
            
        content_type = item[4]
        title = item[2]
        content = item[3]
        
        if content_type == "menu":
            # Переход в подменю
            menu_title = format_menu_item_display(title, content_type, True)
            keyboard = build_keyboard(item_id, callback.from_user.id)
            
            # Проверяем, есть ли у кнопки изображение
            button_image_path = item[9]  # image_path находится под индексом 9
            has_button_image = button_image_path and button_image_path.strip()
            
            if has_button_image:
                # У кнопки есть изображение - отправляем новое сообщение с изображением
                image_full_path = os.path.join(MEDIA_PATH, button_image_path)
                if os.path.exists(image_full_path):
                    try:
                        # Удаляем старое сообщение
                        await safe_delete_message(callback.message)
                        
                        # Отправляем новое сообщение с изображением кнопки
                        photo = FSInputFile(image_full_path)
                        await callback.message.answer_photo(
                            photo=photo,
                            caption=menu_title,
                            reply_markup=keyboard
                        )
                        return
                    except Exception as e:
                        print(f"Ошибка отправки изображения кнопки: {e}")
                        # Если не удалось отправить изображение, продолжаем как обычно
            
            # У кнопки нет изображения или произошла ошибка - отправляем текстовое сообщение
            try:
                # Удаляем старое сообщение с изображением
                await safe_delete_message(callback.message)
                
                # Отправляем новое текстовое сообщение
                await callback.message.answer(
                    menu_title,
                    reply_markup=keyboard
                )
            except Exception:
                # Если удаление не удалось, пытаемся редактировать
                try:
                    await callback.message.edit_text(
                        menu_title, 
                        reply_markup=keyboard
                    )
                except Exception:
                    try:
                        await callback.message.edit_caption(
                            caption=menu_title, 
                            reply_markup=keyboard
                        )
                    except Exception:
                        await callback.message.edit_reply_markup(
                            reply_markup=keyboard
                        )
                    
        elif content_type == "text":
            # Показываем текстовое сообщение
            formatted_title = format_menu_item_display(title, content_type)
            message_text = f"{formatted_title}:\n{content}"
            await callback.message.answer(message_text, reply_markup=close_text_keyboard())
            
        # Удаляем обработку "link" - теперь это URL-кнопки
        # elif content_type == "link": - не нужно, обрабатывается как URL-кнопка
            
        elif content_type == "post_link":
            # Показываем пост с ссылкой (этот тип всё ещё может использоваться для особых случаев)
            formatted_title = format_menu_item_display(title, content_type)
            message_text = f"{formatted_title}\n{content}"
            await callback.message.answer(message_text)

    @dp.callback_query(F.data == "close_text")
    async def close_text_callback(callback: types.CallbackQuery):
        """Закрытие текстового сообщения"""
        await safe_delete_message(callback.message)
