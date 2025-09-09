"""Обработчик навигации по меню"""

import os
from aiogram import types, F
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext
from ...keyboards.keyboards import build_keyboard, close_text_keyboard
from ...database import get_menu_item
from ..common.utils import safe_delete_message, format_menu_item_display, show_main_menu_for_callback, safe_edit_message
from ...utils.texts import *
from ...config.config import MEDIA_PATH

def register_navigation(dp):

    @dp.callback_query(F.data.startswith("nav:"))
    async def navigate(callback: types.CallbackQuery, state: FSMContext):
        """Обработчик навигации по меню"""
        data = callback.data.replace("nav:", "")
        
        # Удаляем предыдущее сообщение со статистикой при любой навигации
        state_data = await state.get_data()
        prev_stats_msg_id = state_data.get('stats_message_id')
        if prev_stats_msg_id:
            try:
                await callback.bot.delete_message(callback.message.chat.id, prev_stats_msg_id)
            except:
                pass  # Игнорируем ошибки, если сообщение уже удалено
            # Очищаем ID из состояния
            await state.update_data(stats_message_id=None)
        
        if data == "root":
            # Возвращаемся к главному меню - показываем logo.JPG
            await safe_delete_message(callback.message)
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
            button_image_path = item[6]  # image_path находится под индексом 6
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
                    await safe_edit_message(
                        callback.message, 
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
            
        elif content_type == "stats":
            # Сбрасываем анимацию кнопки сразу
            await callback.answer()
            
            # Показываем статистику плагинов
            from ...database.plugin_stats import format_plugin_stats_message
            message_text = format_plugin_stats_message()
            
            # Проверяем, есть ли уже сообщение со статистикой
            state_data = await state.get_data()
            prev_stats_msg_id = state_data.get('stats_message_id')
            
            if prev_stats_msg_id:
                # Сообщение существует - пытаемся редактировать его
                try:
                    await callback.bot.edit_message_text(
                        chat_id=callback.message.chat.id,
                        message_id=prev_stats_msg_id,
                        text=message_text,
                        reply_markup=close_text_keyboard()
                    )
                    # Редактирование удалось, выходим
                    return
                except Exception as e:
                    # Если редактирование не удалось, очищаем ID и создаем новое сообщение
                    await state.update_data(stats_message_id=None)
            
            # Создаем новое сообщение со статистикой
            stats_message = await callback.message.answer(message_text, reply_markup=close_text_keyboard())
            await state.update_data(stats_message_id=stats_message.message_id)
            
        elif content_type == "review":
            # Показываем форму отзыва
            await callback.answer()
            from .review_handler import show_review_form
            await show_review_form(callback.message, state)

    @dp.callback_query(F.data == "close_text")
    async def close_text_callback(callback: types.CallbackQuery, state: FSMContext):
        """Закрытие текстового сообщения"""
        await safe_delete_message(callback.message)
        # Очищаем ID сообщения со статистикой
        await state.update_data(stats_message_id=None)
