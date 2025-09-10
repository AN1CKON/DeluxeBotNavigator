"""Обработчики для управления статистикой плагинов"""

import asyncio
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from src.handlers.common.utils import safe_delete_message
from src.models import AdminStates
from src.database.plugin_stats import get_all_plugin_stats, add_plugin_stat, update_plugin_stat, get_plugin_stat_by_id
from src.keyboards.keyboards_admin import cancel_button

def register_stats_handlers(dp):
    """Регистрация обработчиков управления статистикой плагинов"""

    @dp.callback_query(F.data == "add_plugin_stat")
    async def add_plugin_stat_callback(callback: types.CallbackQuery, state: FSMContext):
        """Добавление новой статистики плагина"""
        await safe_delete_message(callback.message)
        await state.set_state(AdminStates.waiting_for_plugin_name)
        await callback.message.answer("📝 Введите название плагина:", reply_markup=cancel_button())

    @dp.callback_query(F.data == "edit_plugin_stats")
    async def edit_plugin_stats_callback(callback: types.CallbackQuery, state: FSMContext):
        """Вход в режим редактирования плагинов"""
        await safe_delete_message(callback.message)
        await state.set_state(AdminStates.editing_plugin_mode)
        await state.update_data(selected_plugin_id=None)
        await show_plugin_edit_list(callback.message, state)

    @dp.callback_query(F.data.startswith("select_plugin:"))
    async def select_plugin_callback(callback: types.CallbackQuery, state: FSMContext):
        """Выбор плагина для редактирования"""
        plugin_id = int(callback.data.split(":")[1])
        data = await state.get_data()
        current_selected = data.get('selected_plugin_id')

        # Переключаем выделение
        new_selected = None if current_selected == plugin_id else plugin_id
        await state.update_data(selected_plugin_id=new_selected)
        await update_plugin_edit_interface(callback, state)

    @dp.callback_query(F.data == "edit_plugin_name")
    async def edit_plugin_name_callback(callback: types.CallbackQuery, state: FSMContext):
        """Изменение имени плагина"""
        data = await state.get_data()
        plugin_id = data.get('selected_plugin_id')

        if not plugin_id:
            await callback.answer("❌ Выберите плагин сначала", show_alert=True)
            return

        plugin = get_plugin_stat_by_id(plugin_id)
        if not plugin:
            await callback.answer("❌ Плагин не найден", show_alert=True)
            return

        await safe_delete_message(callback.message)
        await state.set_state(AdminStates.waiting_for_edit_plugin_name)
        name_request_msg = await callback.message.answer(
            f"📝 Текущее название: {plugin['name']}\n\nВведите новое название:",
            reply_markup=cancel_button()
        )
        await state.update_data(name_request_msg_id=name_request_msg.message_id)

    @dp.callback_query(F.data == "change_plugin_status")
    async def change_plugin_status_callback(callback: types.CallbackQuery, state: FSMContext):
        """Изменение статуса плагина"""
        data = await state.get_data()
        plugin_id = data.get('selected_plugin_id')

        if not plugin_id:
            await callback.answer("❌ Выберите плагин сначала", show_alert=True)
            return

        plugin = get_plugin_stat_by_id(plugin_id)
        if not plugin:
            await callback.answer("❌ Плагин не найден", show_alert=True)
            return

        if plugin['status'] == 'актуален':
            # Запрос процента для статуса "на обновлении"
            await safe_delete_message(callback.message)
            await state.set_state(AdminStates.waiting_for_plugin_progress)
            progress_request_msg = await callback.message.answer(
                f"📊 Для плагина '{plugin['name']}' укажите процент готовности обновления (0-100):",
                reply_markup=cancel_button()
            )
            await state.update_data(progress_request_msg_id=progress_request_msg.message_id)
        else:
            # Изменение на "актуален"
            if update_plugin_stat(plugin_id, status='актуален', progress=0):
                success_msg = await callback.message.answer("✅ Статус изменен!")
                await asyncio.sleep(2)
                await success_msg.delete()
                await update_plugin_edit_interface(callback, state)
            else:
                await callback.answer("❌ Ошибка изменения статуса", show_alert=True)

    @dp.callback_query(F.data == "back_to_stats_main")
    async def back_to_stats_main_callback(callback: types.CallbackQuery, state: FSMContext):
        """Возврат к главному меню управления статистикой"""
        await safe_delete_message(callback.message)
        await state.clear()
        await show_stats_management(callback.message)

    @dp.callback_query(F.data == "cancel_plugin_stat")
    async def cancel_plugin_stat(callback: types.CallbackQuery, state: FSMContext):
        """Отмена добавления статистики"""
        await state.clear()
        await show_stats_management(callback.message)

    @dp.callback_query(F.data == "plugin_status_up_to_date")
    async def plugin_status_up_to_date(callback: types.CallbackQuery, state: FSMContext):
        """Статус: актуален"""
        data = await state.get_data()
        plugin_name = data.get('plugin_name')

        if add_plugin_stat(plugin_name, 'актуален'):
            success_msg = await callback.message.answer("✅ Статистика добавлена!")
            await asyncio.sleep(2)
            await success_msg.delete()
            await state.clear()
            await show_stats_management(callback.message)
        else:
            await callback.answer("❌ Ошибка добавления", show_alert=True)

    @dp.callback_query(F.data == "plugin_status_updating")
    async def plugin_status_updating(callback: types.CallbackQuery, state: FSMContext):
        """Статус: на обновлении"""
        await state.set_state(AdminStates.waiting_for_plugin_progress)
        await callback.message.edit_text(
            "📊 Укажите процент готовности обновления (0-100):",
            reply_markup=cancel_button()
        )

    # Обработчики сообщений
    @dp.message(AdminStates.waiting_for_plugin_name)
    async def process_plugin_name(message: types.Message, state: FSMContext):
        """Обработка названия плагина"""
        plugin_name = message.text.strip()
        if not plugin_name:
            error_msg = await message.answer("❌ Название не может быть пустым. Попробуйте снова:")
            await asyncio.sleep(3)
            await message.delete()
            await error_msg.delete()
            return

        await state.update_data(plugin_name=plugin_name)
        await state.set_state(AdminStates.waiting_for_plugin_status)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Актуален", callback_data="plugin_status_up_to_date")],
            [InlineKeyboardButton(text="🔄 На обновлении", callback_data="plugin_status_updating")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_plugin_stat")]
        ])

        await message.answer(f"📊 Выберите статус для плагина '{plugin_name}':", reply_markup=keyboard)

    @dp.message(AdminStates.waiting_for_plugin_progress)
    async def process_plugin_progress(message: types.Message, state: FSMContext):
        """Обработка процента готовности"""
        try:
            progress = int(message.text.strip())
            if not (0 <= progress <= 100):
                raise ValueError
        except ValueError:
            error_msg = await message.answer("❌ Введите число от 0 до 100:")
            await asyncio.sleep(3)
            await message.delete()
            await error_msg.delete()
            return

        data = await state.get_data()
        plugin_id = data.get('selected_plugin_id')
        plugin_name = data.get('plugin_name')

        # Определяем действие: обновление существующего или добавление нового
        if plugin_id:
            success = update_plugin_stat(plugin_id, status='на обновлении', progress=progress)
            success_msg = "✅ Статус изменен!"
            next_action = lambda: show_plugin_edit_list(message, state)
        else:
            success = add_plugin_stat(plugin_name, 'на обновлении', progress)
            success_msg = "✅ Статистика добавлена!"
            next_action = lambda: show_stats_management(message)

        if success:
            success_notification = await message.answer(success_msg)
            await asyncio.sleep(2)
            
            # Удаляем все сообщения: уведомление, сообщение пользователя и запрос процента
            await message.delete()
            await success_notification.delete()
            
            # Удаляем сообщение с запросом процента, если оно сохранено
            progress_request_msg_id = data.get('progress_request_msg_id')
            if progress_request_msg_id:
                try:
                    await message.bot.delete_message(message.chat.id, progress_request_msg_id)
                except:
                    pass  # Игнорируем ошибки, если сообщение уже удалено
            
            await state.clear()  # Это очистит все данные, включая progress_request_msg_id
            await next_action()
        else:
            await message.answer("❌ Ошибка" + (" изменения статуса" if plugin_id else " добавления"))

    @dp.message(AdminStates.waiting_for_edit_plugin_name)
    async def process_edit_plugin_name(message: types.Message, state: FSMContext):
        """Обработка изменения имени плагина"""
        new_name = message.text.strip()
        if not new_name:
            error_msg = await message.answer("❌ Название не может быть пустым. Попробуйте снова:")
            await asyncio.sleep(3)
            await message.delete()
            await error_msg.delete()
            return

        data = await state.get_data()
        plugin_id = data.get('selected_plugin_id')

        if update_plugin_stat(plugin_id, name=new_name):
            success_notification = await message.answer("✅ Название изменено!")
            await asyncio.sleep(2)
            
            # Удаляем все сообщения: уведомление, сообщение пользователя и запрос названия
            await message.delete()
            await success_notification.delete()
            
            # Удаляем сообщение с запросом названия, если оно сохранено
            name_request_msg_id = data.get('name_request_msg_id')
            if name_request_msg_id:
                try:
                    await message.bot.delete_message(message.chat.id, name_request_msg_id)
                except:
                    pass  # Игнорируем ошибки, если сообщение уже удалено
            
            await state.clear()  # Это очистит все данные, включая name_request_msg_id
            await show_plugin_edit_list(message, state)
        else:
            await message.answer("❌ Ошибка изменения названия")

async def show_stats_management(message: types.Message):
    """Показать меню управления статистикой"""
    stats = get_all_plugin_stats()

    text = "⚙️ Управление статистикой плагинов\n\n"
    if stats:
        text += "📋 Текущие плагины:\n"
        for stat in stats:
            progress_text = f" ({stat['progress']}%)" if stat['status'] == 'на обновлении' else ""
            text += f"{stat['name']}\n└─➤ {stat['status'].capitalize()}{progress_text}\n"
    else:
        text += "📋 Нет данных о плагинах"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить плагин", callback_data="add_plugin_stat")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_plugin_stats")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_settings")]
    ])

    await message.answer(text, reply_markup=keyboard)

async def show_plugin_edit_list(message: types.Message, state: FSMContext = None):
    """Показать список плагинов для редактирования с контекстным меню"""
    stats = get_all_plugin_stats()

    text = "✏️ Редактирование плагинов\n\n📋 Выберите плагин для редактирования:\n\n"

    keyboard_buttons = []
    selected_plugin_id = None

    if state:
        data = await state.get_data()
        selected_plugin_id = data.get('selected_plugin_id')

    for stat in stats:
        status_emoji = "✅" if stat['status'] == 'актуален' else "🔄"
        progress_text = f" ({stat['progress']}%)" if stat['status'] == 'на обновлении' else ""
        display_name = f"{status_emoji} {stat['name']}{progress_text}"

        if selected_plugin_id == stat['id']:
            display_name = f"{display_name} 🔸"

        keyboard_buttons.append([
            InlineKeyboardButton(text=display_name, callback_data=f"select_plugin:{stat['id']}")
        ])

        # Контекстные кнопки под выбранным плагином
        if selected_plugin_id == stat['id']:
            control_buttons = [
                InlineKeyboardButton(text="📝 Изменить имя", callback_data="edit_plugin_name"),
                InlineKeyboardButton(
                    text="🔄 На обновлении" if stat['status'] == 'актуален' else "✅ Сделать актуальным",
                    callback_data="change_plugin_status"
                )
            ]
            keyboard_buttons.append(control_buttons)

    keyboard_buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_stats_main")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(text, reply_markup=keyboard)

async def update_plugin_edit_interface(callback: types.CallbackQuery, state: FSMContext):
    """Обновить интерфейс редактирования плагинов в текущем сообщении"""
    stats = get_all_plugin_stats()

    text = "✏️ Редактирование плагинов\n\n📋 Выберите плагин для редактирования:\n\n"

    keyboard_buttons = []
    data = await state.get_data()
    selected_plugin_id = data.get('selected_plugin_id')

    for stat in stats:
        status_emoji = "✅" if stat['status'] == 'актуален' else "🔄"
        progress_text = f" ({stat['progress']}%)" if stat['status'] == 'на обновлении' else ""
        display_name = f"{status_emoji} {stat['name']}{progress_text}"

        if selected_plugin_id == stat['id']:
            display_name = f"{display_name} 🔸"

        keyboard_buttons.append([
            InlineKeyboardButton(text=display_name, callback_data=f"select_plugin:{stat['id']}")
        ])

        # Контекстные кнопки под выбранным плагином
        if selected_plugin_id == stat['id']:
            control_buttons = [
                InlineKeyboardButton(text="📝 Изменить имя", callback_data="edit_plugin_name"),
                InlineKeyboardButton(
                    text="🔄 На обновлении" if stat['status'] == 'актуален' else "✅ Сделать актуальным",
                    callback_data="change_plugin_status"
                )
            ]
            keyboard_buttons.append(control_buttons)

    keyboard_buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_stats_main")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)
