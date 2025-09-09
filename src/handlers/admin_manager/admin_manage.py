"""Обработчик управления администраторами"""

import asyncio
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from ..common.utils import is_admin, is_super_admin, safe_delete_message
from ...models.states import AdminStates
from ...utils.texts import (
    MSG_ADD_ADMIN_INSTRUCTION,
    MSG_ADMIN_ADDED_SUCCESS,
    MSG_REMOVE_ADMIN_INSTRUCTION,
    MSG_ADMIN_REMOVED_SUCCESS,
    MSG_ADMIN_NO_REGULAR_ADMINS,
    MSG_ADMIN_ALREADY_EXISTS,
    MSG_ADMIN_CANNOT_REMOVE_SUPER,
    MSG_ADMIN_NOT_ADMIN,
    MSG_ADMIN_ADD_ERROR,
    MSG_ADMIN_REMOVE_ERROR,
    MSG_ADMIN_ACCESS_DENIED,
    MSG_ADMIN_ACCESS_DENIED_SHORT,
    MSG_ADMIN_UPDATE_INSTRUCTION,
    MSG_ADMIN_UPDATE_PROGRESS,
    MSG_ADMIN_UPDATE_SUCCESS,
    MSG_ADMIN_UPDATE_NO_CHANGES,
    BUTTON_MANAGE_SUPER_ADMINS
)
from .admin_manage_db import AdminUserManager, AdminDataManager, AdminValidator
from .admin_manage_ui import (
    AdminMessageHandler, 
    AdminMenuBuilder, 
    AdminKeyboardBuilder, 
    AdminUIHelper
)


def register_admin_manage(dp, bot):
    """Регистрация всех обработчиков управления администраторами"""

    @dp.callback_query(F.data == "manage_admins")
    async def manage_admins_callback(callback: types.CallbackQuery):
        """Показывает меню управления администраторами"""
        if not is_super_admin(callback.from_user.id):
            return await callback.answer(MSG_ADMIN_ACCESS_DENIED, show_alert=True)
        
        # Обновляем информацию об администраторе
        AdminDataManager.update_admin_info(
            callback.from_user.id, 
            callback.from_user.username, 
            callback.from_user.first_name
        )
        await safe_delete_message(callback.message)
        await AdminUIHelper.show_admin_manage_menu(callback.message)

    @dp.callback_query(F.data == "manage_super_admins")
    async def manage_super_admins_callback(callback: types.CallbackQuery):
        """Показывает меню управления супер-администраторами"""
        if not is_super_admin(callback.from_user.id):
            return await callback.answer(MSG_ADMIN_ACCESS_DENIED, show_alert=True)
        
        await safe_delete_message(callback.message)
        await show_super_admin_management_menu(callback.message)

    @dp.callback_query(F.data == "add_admin")
    async def add_admin_callback(callback: types.CallbackQuery, state: FSMContext):
        """Начинает процесс добавления администратора"""
        if not is_super_admin(callback.from_user.id):
            return await callback.answer(MSG_ADMIN_ACCESS_DENIED_SHORT, show_alert=True)
        
        await safe_delete_message(callback.message)
        await state.set_state(AdminStates.waiting_for_new_admin_id)
        
        await callback.message.answer(
            MSG_ADD_ADMIN_INSTRUCTION, 
            reply_markup=AdminKeyboardBuilder.build_cancel_keyboard()
        )

    @dp.message(AdminStates.waiting_for_new_admin_id)
    async def process_new_admin_id(message: types.Message, state: FSMContext):
        """Обрабатывает ID нового администратора"""
        if not is_super_admin(message.from_user.id):
            return await message.answer(MSG_ADMIN_ACCESS_DENIED_SHORT)
        
        # Валидация ID
        is_valid, user_id, error_msg = AdminValidator.validate_user_id(message.text)
        if not is_valid:
            await AdminMessageHandler.send_countdown_message(message, error_msg)
            return
        
        # Проверка на существование администратора
        if AdminValidator.check_admin_exists(user_id):
            await AdminMessageHandler.send_countdown_message(message, MSG_ADMIN_ALREADY_EXISTS)
            return
        
        # Добавление администратора с получением информации
        success, user_info = await AdminUserManager.add_admin_with_info(
            bot=message.bot,
            user_id=user_id,
            added_by=message.from_user.id,
            chat_id=message.chat.id
        )
        
        if success:
            # Очищаем сообщения
            await AdminMessageHandler.clear_chat_messages(
                message.bot, message.chat.id, message.message_id, 10
            )
            
            # Формируем сообщение об успехе
            base_message = MSG_ADMIN_ADDED_SUCCESS.format(admin_id=user_id)
            success_msg = AdminMenuBuilder.build_success_message_with_info(base_message, user_info)
            
            # Показываем сообщение с кнопкой ОК
            await message.answer(
                success_msg,
                reply_markup=AdminKeyboardBuilder.build_success_keyboard(user_id)
            )
            await state.clear()
        else:
            await AdminMessageHandler.send_countdown_message(message, MSG_ADMIN_ADD_ERROR)

    @dp.callback_query(F.data == "remove_admin")
    async def remove_admin_callback(callback: types.CallbackQuery, state: FSMContext):
        """Начинает процесс удаления администратора"""
        if not is_super_admin(callback.from_user.id):
            return await callback.answer(MSG_ADMIN_ACCESS_DENIED_SHORT, show_alert=True)
        
        await safe_delete_message(callback.message)
        
        # Получаем список обычных администраторов
        regular_admins = AdminDataManager.get_regular_admins()
        
        if not regular_admins:
            await callback.message.answer(
                MSG_ADMIN_NO_REGULAR_ADMINS, 
                reply_markup=AdminKeyboardBuilder.build_back_keyboard()
            )
            return
        
        await state.set_state(AdminStates.waiting_for_remove_admin_id)
        
        # Формируем список администраторов для удаления
        admin_list = AdminMenuBuilder.build_admin_removal_list(regular_admins)
        text = MSG_REMOVE_ADMIN_INSTRUCTION.format(admin_list=admin_list)
        
        await callback.message.answer(
            text, 
            reply_markup=AdminKeyboardBuilder.build_cancel_keyboard(), 
            parse_mode="HTML"
        )

    @dp.message(AdminStates.waiting_for_remove_admin_id)
    async def process_remove_admin_id(message: types.Message, state: FSMContext):
        """Обрабатывает ID администратора для удаления"""
        if not is_super_admin(message.from_user.id):
            return await message.answer(MSG_ADMIN_ACCESS_DENIED_SHORT)
        
        # Валидация ID
        is_valid, user_id, error_msg = AdminValidator.validate_user_id(message.text)
        if not is_valid:
            await AdminMessageHandler.send_countdown_message(message, error_msg)
            return
        
        # Проверки безопасности
        if AdminValidator.check_is_super_admin(user_id):
            await AdminMessageHandler.send_countdown_message(message, MSG_ADMIN_CANNOT_REMOVE_SUPER)
            return
        
        if not AdminValidator.check_admin_exists(user_id):
            await AdminMessageHandler.send_countdown_message(message, MSG_ADMIN_NOT_ADMIN)
            return
        
        # Получаем информацию об администраторе и удаляем
        admin_info = AdminDataManager.get_admin_info(user_id)
        admin_name = AdminDataManager.format_admin_name(admin_info)
        
        if AdminDataManager.remove_admin(user_id):
            await AdminMessageHandler.clear_chat_messages(
                message.bot, message.chat.id, message.message_id, 5
            )
            await AdminMessageHandler.send_countdown_message(
                message, 
                MSG_ADMIN_REMOVED_SUCCESS.format(admin_name=admin_name, admin_id=user_id)
            )
            await AdminUIHelper.show_admin_manage_menu(message)
            await state.clear()
        else:
            await AdminMessageHandler.send_countdown_message(message, MSG_ADMIN_REMOVE_ERROR)

    @dp.callback_query(F.data == "list_admins")
    async def list_admins_callback(callback: types.CallbackQuery):
        """Показывает подробный список администраторов"""
        if not is_super_admin(callback.from_user.id):
            return await callback.answer(MSG_ADMIN_ACCESS_DENIED_SHORT, show_alert=True)
        
        await safe_delete_message(callback.message)
        admins = AdminDataManager.get_all_admins()
        text = AdminMenuBuilder.build_detailed_admin_list_text(admins)
        
        await callback.message.answer(
            text, 
            reply_markup=AdminKeyboardBuilder.build_back_keyboard(), 
            parse_mode="HTML"
        )

    @dp.callback_query(F.data == "update_admin_info")
    async def update_admin_info_callback(callback: types.CallbackQuery):
        """Обновляет информацию об администраторах"""
        if not is_super_admin(callback.from_user.id):
            return await callback.answer(MSG_ADMIN_ACCESS_DENIED_SHORT, show_alert=True)
        
        await safe_delete_message(callback.message)
        
        # Показываем инструкцию с подтверждением
        await callback.message.answer(
            MSG_ADMIN_UPDATE_INSTRUCTION,
            reply_markup=AdminKeyboardBuilder.build_confirmation_keyboard("confirm_update_admin_info")
        )

    @dp.callback_query(F.data == "confirm_update_admin_info")
    async def confirm_update_admin_info_callback(callback: types.CallbackQuery):
        """Подтверждает и выполняет обновление информации об администраторах"""
        if not is_super_admin(callback.from_user.id):
            return await callback.answer(MSG_ADMIN_ACCESS_DENIED_SHORT, show_alert=True)
        
        await safe_delete_message(callback.message)
        
        # Показываем прогресс
        progress_msg = await AdminUIHelper.show_progress_message(
            callback.message, 
            MSG_ADMIN_UPDATE_PROGRESS
        )
        
        # Обновляем информацию
        updated_count = await AdminUserManager.update_all_admins_info(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id
        )
        
        # Показываем результат
        if updated_count > 0:
            result_text = MSG_ADMIN_UPDATE_SUCCESS.format(count=updated_count)
        else:
            result_text = MSG_ADMIN_UPDATE_NO_CHANGES
        
        await AdminUIHelper.update_progress_message(progress_msg, result_text)
        
        # Через 3 секунды показываем обновленный список
        await asyncio.sleep(3)
        await safe_delete_message(progress_msg)
        await AdminUIHelper.show_admin_manage_menu(callback.message)

    @dp.callback_query(F.data.startswith("admin_added_ok:"))
    async def admin_added_ok_callback(callback: types.CallbackQuery):
        """Обработчик кнопки ОК после успешного добавления администратора"""
        await callback.answer()
        
        # Удаляем сообщение с кнопкой ОК
        await safe_delete_message(callback.message)
        
        # Показываем меню управления администраторами
        await AdminUIHelper.show_admin_manage_menu(callback.message)


    @dp.callback_query(F.data.startswith("promote_super:"))
    async def promote_super_admin_callback(callback: types.CallbackQuery):
        """Повышает администратора до супер-администратора"""
        if not is_super_admin(callback.from_user.id):
            return await callback.answer(MSG_ADMIN_ACCESS_DENIED_SHORT, show_alert=True)
        
        user_id = int(callback.data.split(":")[1])
        
        from ...database import promote_to_super_admin
        if promote_to_super_admin(user_id):
            await callback.answer("✅ Администратор повышен до супер-администратора!")
            await safe_delete_message(callback.message)
            await show_super_admin_management_menu(callback.message)
        else:
            await callback.answer("❌ Ошибка повышения администратора", show_alert=True)

    @dp.callback_query(F.data.startswith("demote_super:"))
    async def demote_super_admin_callback(callback: types.CallbackQuery):
        """Понижает супер-администратора до обычного администратора"""
        if not is_super_admin(callback.from_user.id):
            return await callback.answer(MSG_ADMIN_ACCESS_DENIED_SHORT, show_alert=True)
        
        from ...config.config import ADMIN_ID
        user_id = int(callback.data.split(":")[1])
        
        # Проверяем, что не пытаемся понизить создателя
        if user_id == ADMIN_ID:
            return await callback.answer("❌ Нельзя понизить создателя бота!", show_alert=True)
        
        # Проверяем, что не пытаемся понизить себя
        if user_id == callback.from_user.id:
            return await callback.answer("❌ Вы не можете понизить себя!", show_alert=True)
        
        from ...database import demote_from_super_admin
        if demote_from_super_admin(user_id):
            await callback.answer("✅ Супер-администратор понижен до обычного администратора!")
            await safe_delete_message(callback.message)
            await show_super_admin_management_menu(callback.message)
        else:
            await callback.answer("❌ Ошибка понижения администратора", show_alert=True)


async def show_super_admin_management_menu(message: types.Message, bot=None):
    """Показывает меню управления супер-администраторами"""
    from ...database import get_all_admins, promote_to_super_admin, demote_from_super_admin
    from ...config.config import ADMIN_ID
    
    admins = get_all_admins()
    
    text = "👑 Управление супер-администраторами\n\n"
    
    if not admins:
        text += "📋 Администраторов не найдено"
    else:
        # Разделяем на супер-админов и обычных админов
        super_admins = [admin for admin in admins if admin['is_super_admin']]
        regular_admins = [admin for admin in admins if not admin['is_super_admin']]
        
        text += f"⭐ Супер-администраторы ({len(super_admins)}):\n"
        for admin in super_admins:
            username = f"@{admin['username']}" if admin['username'] else "без username"
            name = admin['first_name'] or "без имени"
            creator_mark = " 👑" if admin['user_id'] == ADMIN_ID else ""
            text += f"• {admin['user_id']} - {name} {username}{creator_mark}\n"
        
        if regular_admins:
            text += f"\n👤 Обычные администраторы ({len(regular_admins)}):\n"
            for admin in regular_admins:
                username = f"@{admin['username']}" if admin['username'] else "без username"
                name = admin['first_name'] or "без имени"
                text += f"• {admin['user_id']} - {name} {username}\n"
    
    # Создаем клавиатуру
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    
    # Добавляем кнопки для каждого обычного админа (повысить до супер-админа)
    for admin in regular_admins:
        # Получаем отображаемое имя пользователя
        display_name = admin['username'] or admin['first_name'] or f"ID:{admin['user_id']}"
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(
                text=f"Повысить {display_name}", 
                callback_data=f"promote_super:{admin['user_id']}"
            )
        ])
    
    # Добавляем кнопки для каждого супер-админа (понизить до обычного админа)
    for admin in super_admins:
        # Не показываем кнопку понижения для создателя
        if admin['user_id'] == ADMIN_ID:
            continue
            
        # Получаем отображаемое имя пользователя
        display_name = admin['username'] or admin['first_name'] or f"ID:{admin['user_id']}"
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(
                text=f"Понизить {display_name}", 
                callback_data=f"demote_super:{admin['user_id']}"
            )
        ])
    
    # Кнопка назад
    keyboard.inline_keyboard.append([
        types.InlineKeyboardButton(text="⬅️ Назад", callback_data="manage_admins")
    ])
    
    await message.answer(text, reply_markup=keyboard)
