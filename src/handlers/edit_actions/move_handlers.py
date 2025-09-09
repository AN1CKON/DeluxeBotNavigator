"""Базовые обработчики для перемещения кнопок"""

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from ..common.utils import safe_delete_message, safe_edit_message
from ...models.states import MenuState
from ...database.positioning.core import (
    move_button_up, move_button_down, group_buttons, ungroup_buttons,
    move_group_up, move_group_down, get_button_groups
)
from ...database import get_menu_item
from ...keyboards.move_keyboards import build_new_ungroup_keyboard, build_ungroup_mode_keyboard
from ...utils.texts import MSG_UNGROUP_MODE_ACTIVE, MSG_UNGROUP_MODE_INSTRUCTIONS, MSG_ERROR_NO_GROUPS
from .move_utils import (
    MoveStateManager, MoveKeyboardBuilder, MessageTextBuilder, CallbackDataExtractor
)
from . import edit_menu


class BaseMoveHandlers:
    """Базовые обработчики для перемещения"""
    
    @staticmethod
    async def show_move_menu(message, state: FSMContext):
        """Показать меню режима перемещения кнопок"""
        await state.set_state(MenuState.move_mode)
        await MoveStateManager.init_move_state(state)
        
        text = MessageTextBuilder.get_default_move_text()
        keyboard = await MoveKeyboardBuilder.build_keyboard_with_state(state)
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    
    @staticmethod
    async def update_move_interface(callback: types.CallbackQuery, state: FSMContext, 
                                  preserve_selection: bool = False):
        """Обновить интерфейс перемещения"""
        data = await state.get_data()
        group_mode = data.get('group_mode', False)
        
        if group_mode:
            selected_buttons = data.get('selected_buttons', [])
            text = MessageTextBuilder.get_group_mode_text(selected_buttons)
        else:
            text = MessageTextBuilder.get_default_move_text()
        
        keyboard = await MoveKeyboardBuilder.build_keyboard_with_state(state)
        await safe_edit_message(callback.message, text, reply_markup=keyboard, parse_mode="HTML")


class NavigationHandlers:
    """Обработчики навигации"""
    
    @staticmethod
    def register_handlers(dp):
        """Регистрация обработчиков навигации"""
        
        @dp.callback_query(F.data.startswith("edit_action_back:"))
        async def handle_edit_action_back(callback: types.CallbackQuery, state: FSMContext):
            """Возврат к меню редактирования конкретной кнопки"""
            await safe_delete_message(callback.message)
            item_id = CallbackDataExtractor.extract_item_id(callback.data)
            await edit_menu.show_edit_button_menu(callback.message, item_id, state)
            await callback.answer()
        
        @dp.callback_query(F.data == "move_mode")
        async def handle_move_mode(callback: types.CallbackQuery, state: FSMContext):
            """Переход к режиму перемещения"""
            await safe_delete_message(callback.message)
            await BaseMoveHandlers.show_move_menu(callback.message, state)
            await callback.answer()
        
        @dp.callback_query(F.data == "new_move_mode")
        async def handle_new_move_mode(callback: types.CallbackQuery, state: FSMContext):
            """Возврат к основному режиму перемещения"""
            await safe_delete_message(callback.message)
            await state.set_state(MenuState.move_mode)
            
            # Сохраняем текущее состояние, не сбрасываем current_parent_id
            data = await state.get_data()
            current_parent_id = data.get('current_parent_id')
            await state.update_data(
                selected_buttons=[],
                group_mode=False,
                editing_item_id=None,
                selected_item_id=None,
                selected_group_position=None
                # current_parent_id сохраняется
            )
            
            # Отправляем новое сообщение вместо попытки редактирования удаленного
            text = MessageTextBuilder.get_default_move_text()
            keyboard = await MoveKeyboardBuilder.build_keyboard_with_state(state)
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
        
        @dp.callback_query(F.data.startswith("move_enter_folder:"))
        async def handle_enter_folder(callback: types.CallbackQuery, state: FSMContext):
            """Вход в папку для перемещения дочерних кнопок"""
            folder_id = int(callback.data.split(":")[1])
            
            # Обновляем current_parent_id в состоянии
            await state.update_data(current_parent_id=folder_id)
            
            # Очищаем выборы
            await MoveStateManager.clear_selections(state)
            
            # Обновляем интерфейс
            await BaseMoveHandlers.update_move_interface(callback, state)
            await callback.answer(f"Вошли в папку")
        
        @dp.callback_query(F.data.startswith("move_back_to_parent:"))
        async def handle_back_to_parent(callback: types.CallbackQuery, state: FSMContext):
            """Возврат к родительской папке"""
            parent_id = int(callback.data.split(":")[1])
            
            # Получаем информацию о родительском элементе
            from ...database import get_menu_item
            parent_item = get_menu_item(parent_id)
            
            if parent_item and parent_item[1]:  # Если у родителя есть свой parent_id
                new_parent_id = parent_item[1]
            else:
                new_parent_id = None  # Возврат к корню
            
            # Обновляем current_parent_id в состоянии
            await state.update_data(current_parent_id=new_parent_id)
            
            # Очищаем выборы
            await MoveStateManager.clear_selections(state)
            
            # Обновляем интерфейс
            await BaseMoveHandlers.update_move_interface(callback, state)
            await callback.answer(f"Вернулись к '{parent_item[2] if parent_item else 'корню'}'")
            
        @dp.callback_query(F.data == "admin_panel")
        async def handle_admin_panel_exit(callback: types.CallbackQuery, state: FSMContext):
            """Выход из режима перемещения в админ-панель"""
            await safe_delete_message(callback.message)
            # Очищаем состояние режима перемещения
            await state.clear()
            # Импортируем здесь чтобы избежать циклических импортов
            from ..admin_menu.admin_menu import show_admin_panel
            await show_admin_panel(callback.message)
            await callback.answer()


class MovementHandlers:
    """Обработчики перемещения элементов"""
    
    @staticmethod
    def register_handlers(dp):
        """Регистрация обработчиков перемещения"""
        
        @dp.callback_query(F.data.startswith(("move_up:", "new_move_up:")))
        async def handle_move_up(callback: types.CallbackQuery, state: FSMContext):
            """Перемещение кнопки вверх"""
            item_id = CallbackDataExtractor.extract_item_id(callback.data)
            success = move_button_up(item_id)
            
            if success:
                await callback.answer("✅ Кнопка перемещена вверх")
                await state.update_data(selected_item_id=item_id)
                await BaseMoveHandlers.update_move_interface(callback, state)
            else:
                await callback.answer("❌ Не удалось переместить кнопку", show_alert=True)
        
        @dp.callback_query(F.data.startswith(("move_down:", "new_move_down:")))
        async def handle_move_down(callback: types.CallbackQuery, state: FSMContext):
            """Перемещение кнопки вниз"""
            item_id = CallbackDataExtractor.extract_item_id(callback.data)
            success = move_button_down(item_id)
            
            if success:
                await callback.answer("✅ Кнопка перемещена вниз")
                await state.update_data(selected_item_id=item_id)
                await BaseMoveHandlers.update_move_interface(callback, state)
            else:
                await callback.answer("❌ Не удалось переместить кнопку", show_alert=True)
        
        @dp.callback_query(F.data.startswith(("move_group_up:", "new_move_group_up:")))
        async def handle_move_group_up(callback: types.CallbackQuery, state: FSMContext):
            """Перемещение группы вверх"""
            group_position = CallbackDataExtractor.extract_group_position(callback.data)
            data = await state.get_data()
            current_parent_id = data.get('current_parent_id')
            new_position = move_group_up(group_position, parent_id=current_parent_id)
            
            if new_position is not None:
                await callback.answer("✅ Группа перемещена вверх")
                # Группа остается выбранной на новой позиции
                await state.update_data(selected_group_position=new_position)
                await BaseMoveHandlers.update_move_interface(callback, state)
            else:
                await callback.answer("❌ Не удалось переместить группу", show_alert=True)
        
        @dp.callback_query(F.data.startswith(("move_group_down:", "new_move_group_down:")))
        async def handle_move_group_down(callback: types.CallbackQuery, state: FSMContext):
            """Перемещение группы вниз"""
            group_position = CallbackDataExtractor.extract_group_position(callback.data)
            data = await state.get_data()
            current_parent_id = data.get('current_parent_id')
            new_position = move_group_down(group_position, parent_id=current_parent_id)
            
            if new_position is not None:
                await callback.answer("✅ Группа перемещена вниз")
                # Группа остается выбранной на новой позиции  
                await state.update_data(selected_group_position=new_position)
                await BaseMoveHandlers.update_move_interface(callback, state)
            else:
                await callback.answer("❌ Не удалось переместить группу", show_alert=True)


class ControlHandlers:
    """Обработчики управления элементами"""
    
    @staticmethod
    def register_handlers(dp):
        """Регистрация обработчиков управления"""
        
        @dp.callback_query(F.data.startswith(("move_show_controls:", "new_move_show_controls:")))
        async def handle_show_controls(callback: types.CallbackQuery, state: FSMContext):
            """Показать/скрыть кнопки управления для элемента"""
            item_id = CallbackDataExtractor.extract_item_id(callback.data)
            await MoveStateManager.toggle_item_selection(state, item_id)
            await BaseMoveHandlers.update_move_interface(callback, state)
            await callback.answer()
        
        @dp.callback_query(F.data.startswith(("move_show_group_controls:", "new_move_show_group_controls:")))
        async def handle_show_group_controls(callback: types.CallbackQuery, state: FSMContext):
            """Показать/скрыть кнопки управления для группы"""
            group_position = CallbackDataExtractor.extract_group_position(callback.data)
            await MoveStateManager.toggle_group_selection(state, group_position)
            await BaseMoveHandlers.update_move_interface(callback, state)
            await callback.answer()
