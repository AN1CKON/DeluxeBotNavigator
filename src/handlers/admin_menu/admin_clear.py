"""Обработчик очистки чата"""

from aiogram import types, F
from aiogram.exceptions import TelegramMigrateToChat
from aiogram.types import FSInputFile
from ...config.config import MAX_CLEAR_ATTEMPTS, MAX_DELETE_RANGE, CLEAR_NOTIFICATION_DELAY, get_image_path
from ..common.utils import send_notification_and_cleanup, safe_delete_message
from ...keyboards.keyboards_admin import admin_keyboard
from ...utils.texts import *

def register_admin_clear(dp, bot):
    @dp.callback_query(F.data == "admin_clear")
    async def admin_clear_callback(callback: types.CallbackQuery):
        """Очистка чата от сообщений"""
        chat_id = callback.message.chat.id
        last_id = callback.message.message_id
        deleted_count = 0
        fail_streak = 0
        ids_to_delete = range(last_id, last_id - MAX_DELETE_RANGE, -1)

        # Удаляем сообщения, пока не достигнем лимита ошибок подряд
        for msg_id in ids_to_delete:
            try:
                await bot.delete_message(chat_id, msg_id)
                deleted_count += 1
                fail_streak = 0
            except Exception as e:
                if isinstance(e, TelegramMigrateToChat):
                    chat_id = e.migrate_to_chat_id
                    try:
                        await bot.delete_message(chat_id, msg_id)
                        deleted_count += 1
                        fail_streak = 0
                    except Exception:
                        fail_streak += 1
                else:
                    fail_streak += 1
                    
            if fail_streak >= MAX_CLEAR_ATTEMPTS:
                break

        # Уведомление о результате
        await callback.answer()
        await send_notification_and_cleanup(
            callback.message, 
            MSG_CHAT_CLEARED.format(count=deleted_count),
            delay=CLEAR_NOTIFICATION_DELAY
        )

        # Возвращаем админ-панель
        try:
            photo = FSInputFile(get_image_path("admin.JPG"))
            await bot.send_photo(chat_id, photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())
        except TelegramMigrateToChat as e:
            chat_id = e.migrate_to_chat_id
            photo = FSInputFile(get_image_path("admin.JPG"))
            await bot.send_photo(chat_id, photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())
