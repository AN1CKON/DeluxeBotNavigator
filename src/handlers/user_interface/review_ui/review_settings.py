"""Управление настройками защиты от спама для отзывов"""

import asyncio
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.handlers.common.utils import is_admin, safe_delete_message
from src.models import AdminStates
from src.utils.texts import NO_ACCESS_MESSAGE
from src.handlers.user_interface.review_logic.review_spam_protection import spam_protection
from src.handlers.user_interface.review_ui.review_stats import show_reviews_management

# Глобальная переменная для хранения ID сообщений с cooldown по чатам
cooldown_messages = {}  # {chat_id: message_id}


def register_review_settings_handlers(dp):
    """Регистрация обработчиков для управления настройками защиты от спама"""

    @dp.callback_query(F.data == "change_cooldown")
    async def change_cooldown_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработчик изменения cooldown"""
        global cooldown_messages
        
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)

        # Сбрасываем состояние кнопки сразу
        await callback.answer()

        # Создаем клавиатуру с кнопкой отмены
        cancel_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_cooldown_input")]]
        )

        cooldown_text = ("⏰ <b>Изменение Cooldown</b>\n\n"
                        "📝 Введите новое значение в минутах:\n"
                        "• <code>0</code> - отключить cooldown\n"
                        "• <code>1-1440</code> - установить время в минутах")

        chat_id = callback.message.chat.id
        
        # Проверяем, есть ли уже сообщение с cooldown в этом чате
        if chat_id in cooldown_messages:
            existing_message_id = cooldown_messages[chat_id]
            print(f"Найдено существующее сообщение cooldown для чата {chat_id}: {existing_message_id}")
            # Пытаемся обновить существующее сообщение
            try:
                await callback.message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=existing_message_id,
                    text=cooldown_text,
                    reply_markup=cancel_keyboard,
                    parse_mode="HTML"
                )
                print(f"Сообщение cooldown успешно обновлено для чата {chat_id}")
                # Сообщение успешно обновлено
                await state.set_state(AdminStates.waiting_for_cooldown_value)
                return
            except Exception as e:
                error_message = str(e)
                if "message is not modified" in error_message:
                    # Сообщение не изменилось, просто продолжаем с существующим
                    print(f"Сообщение cooldown не изменилось для чата {chat_id}, продолжаем с существующим")
                    await state.set_state(AdminStates.waiting_for_cooldown_value)
                    return
                else:
                    # Другая ошибка - сообщение не найдено или не может быть обновлено
                    print(f"Не удалось обновить сообщение cooldown: {e}")
                    # Удаляем запись из словаря
                    del cooldown_messages[chat_id]

        print(f"Создаем новое сообщение cooldown для чата {chat_id}")
        # Создаем новое сообщение
        request_msg = await callback.message.answer(
            cooldown_text,
            reply_markup=cancel_keyboard,
            parse_mode="HTML"
        )
        
        # Сохраняем ID нового сообщения в словаре
        cooldown_messages[chat_id] = request_msg.message_id
        print(f"Сохранено новое сообщение cooldown для чата {chat_id}: {request_msg.message_id}")
        await state.set_state(AdminStates.waiting_for_cooldown_value)

    @dp.callback_query(F.data == "cancel_cooldown_input")
    async def cancel_cooldown_input_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработчик отмены ввода cooldown"""
        global cooldown_messages
        
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)

        chat_id = callback.message.chat.id
        
        # Удаляем сообщение с запросом ввода
        if chat_id in cooldown_messages:
            try:
                await callback.message.bot.delete_message(chat_id, cooldown_messages[chat_id])
            except Exception:
                pass
            
            # Удаляем запись из словаря
            del cooldown_messages[chat_id]

        await callback.answer("❌ Ввод отменен", show_alert=True)
        await state.clear()

    @dp.callback_query(F.data == "change_daily_limit")
    async def change_daily_limit_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработчик изменения дневного лимита"""
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)

        await safe_delete_message(callback.message)
        request_msg = await callback.message.answer(
            "📊 Введите новый дневной лимит отзывов (1-50):"
        )
        await state.update_data(request_message_id=request_msg.message_id)
        await state.set_state(AdminStates.waiting_for_daily_limit_value)

    @dp.callback_query(F.data == "reset_settings")
    async def reset_settings_callback(callback: types.CallbackQuery):
        """Обработчик сброса настроек к значениям по умолчанию"""
        if not is_admin(callback.from_user.id):
            return await callback.answer(NO_ACCESS_MESSAGE, show_alert=True)

        # Сбрасываем к значениям по умолчанию
        spam_protection.cooldown_minutes = 0  # Отключаем cooldown по умолчанию
        spam_protection.max_reviews_per_day = 3
        spam_protection.save_settings()

        await callback.answer("✅ Настройки сброшены к значениям по умолчанию", show_alert=True)
        await safe_delete_message(callback.message)
        await show_review_settings_menu(callback.message)

    @dp.message(AdminStates.waiting_for_cooldown_value)
    async def handle_cooldown_value(message: types.Message, state: FSMContext):
        """Обработка ввода значения cooldown"""
        global cooldown_messages
        
        if not is_admin(message.from_user.id):
            await state.clear()
            return

        chat_id = message.chat.id

        try:
            value = int(message.text.strip())
            if value < 0 or value > 1440:
                # Показываем ошибку с таймером
                error_msg = await message.answer(
                    "❌ <b>Ошибка</b>\n"
                    "Значение должно быть от 0 до 1440",
                    parse_mode="HTML"
                )
                
                # Таймер обратного отсчета
                for i in range(3, 0, -1):
                    await asyncio.sleep(1)
                    try:
                        await error_msg.edit_text(
                            f"❌ <b>Ошибка</b>\n"
                            f"Значение должно быть от 0 до 1440\n\n"
                            f"⏰ Закроется через {i} сек...",
                            parse_mode="HTML"
                        )
                    except Exception:
                        break

                # Удаляем сообщения
                await safe_delete_message(error_msg)
                await safe_delete_message(message)
                if chat_id in cooldown_messages:
                    try:
                        await message.bot.delete_message(chat_id, cooldown_messages[chat_id])
                    except Exception:
                        pass
                    
                    # Удаляем запись из словаря
                    del cooldown_messages[chat_id]

                await show_review_settings_menu(message)
                await state.clear()
                return

            spam_protection.cooldown_minutes = value
            spam_protection.save_settings()

            status = "отключен" if value == 0 else f"установлен на {value} мин"
            
            # Показываем успех с таймером
            success_msg = await message.answer(f"✅ Cooldown {status}")
            
            # Таймер обратного отсчета
            for i in range(3, 0, -1):
                await asyncio.sleep(1)
                try:
                    await success_msg.edit_text(
                        f"✅ Cooldown {status}\n\n"
                        f"⏰ Закроется через {i} сек..."
                    )
                except Exception:
                    break

            # Удаляем сообщения
            await safe_delete_message(success_msg)
            await safe_delete_message(message)
            if chat_id in cooldown_messages:
                try:
                    await message.bot.delete_message(chat_id, cooldown_messages[chat_id])
                except Exception:
                    pass
                
                # Удаляем запись из словаря
                del cooldown_messages[chat_id]

            await show_review_settings_menu(message)
            await state.clear()

        except ValueError:
            # Показываем ошибку с таймером для неправильного формата
            error_msg = await message.answer(
                "❌ <b>Ошибка</b>\n"
                "Значение должно быть от 0 до 1440",
                parse_mode="HTML"
            )
            
            # Таймер обратного отсчета
            for i in range(3, 0, -1):
                await asyncio.sleep(1)
                try:
                    await error_msg.edit_text(
                        f"❌ <b>Ошибка</b>\n"
                        f"Значение должно быть от 0 до 1440\n\n"
                        f"⏰ Закроется через {i} сек...",
                        parse_mode="HTML"
                    )
                except Exception:
                    break

            # Удаляем сообщения
            await safe_delete_message(error_msg)
            await safe_delete_message(message)
            if chat_id in cooldown_messages:
                try:
                    await message.bot.delete_message(chat_id, cooldown_messages[chat_id])
                except Exception:
                    pass
                
                # Удаляем запись из словаря
                del cooldown_messages[chat_id]

            await show_review_settings_menu(message)
            await state.clear()
            return

        await state.clear()

    @dp.message(AdminStates.waiting_for_daily_limit_value)
    async def handle_daily_limit_value(message: types.Message, state: FSMContext):
        """Обработка ввода значения дневного лимита"""
        if not is_admin(message.from_user.id):
            await state.clear()
            return

        data = await state.get_data()
        request_message_id = data.get('request_message_id')

        try:
            value = int(message.text.strip())
            if value < 1 or value > 50:
                error_msg = await message.answer("❌ Значение должно быть от 1 до 50 отзывов")
                await asyncio.sleep(2)

                # Удаляем сообщения
                await safe_delete_message(error_msg)
                await safe_delete_message(message)
                if request_message_id:
                    try:
                        await message.bot.delete_message(message.chat.id, request_message_id)
                    except Exception:
                        pass

                await show_review_settings_menu(message)
                return

            spam_protection.max_reviews_per_day = value
            spam_protection.save_settings()

            success_msg = await message.answer(f"✅ Дневной лимит установлен на {value} отзывов")
            await asyncio.sleep(2)

            # Удаляем сообщения
            await safe_delete_message(success_msg)
            await safe_delete_message(message)
            if request_message_id:
                try:
                    await message.bot.delete_message(message.chat.id, request_message_id)
                except Exception:
                    pass

            await show_review_settings_menu(message)

        except ValueError:
            error_msg = await message.answer("❌ Введите число от 1 до 50")
            await asyncio.sleep(2)

            # Удаляем сообщения
            await safe_delete_message(error_msg)
            await safe_delete_message(message)
            if request_message_id:
                try:
                    await message.bot.delete_message(message.chat.id, request_message_id)
                except Exception:
                    pass

            await show_review_settings_menu(message)
            return

        await state.clear()


async def show_review_settings_menu(message: types.Message):
    """Показывает меню настройки параметров защиты от спама"""
    text = f"""<b>⚙️ Настройки защиты от спама</b>

<b>Текущие параметры:</b>
⏰ Cooldown: {"отключен" if spam_protection.cooldown_minutes == 0 else f"{spam_protection.cooldown_minutes} мин"}
📊 Максимум отзывов в день: {spam_protection.max_reviews_per_day}

<b>Выберите параметр для изменения:</b>"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏰ Cooldown", callback_data="change_cooldown"),
             InlineKeyboardButton(text="📊 Дневной лимит", callback_data="change_daily_limit")],
            [InlineKeyboardButton(text="🔄 Сбросить по умолчанию", callback_data="reset_settings")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="manage_reviews"),
             InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_settings")]
        ]
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
