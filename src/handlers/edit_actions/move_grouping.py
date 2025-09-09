"""Обработчики группировки кнопок"""

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from ..common.utils import safe_delete_message, safe_edit_message
from ...database.positioning.core import group_buttons, ungroup_buttons, get_button_groups
from ...database import get_menu_item
from ...keyboards.move_keyboards import build_new_ungroup_keyboard, build_ungroup_mode_keyboard
from ...utils.texts import MSG_UNGROUP_MODE_ACTIVE, MSG_UNGROUP_MODE_INSTRUCTIONS, MSG_ERROR_NO_GROUPS
from .move_utils import (
    MoveStateManager, MoveKeyboardBuilder, MessageTextBuilder, CallbackDataExtractor
)
from .move_handlers import BaseMoveHandlers


class GroupingHandlers:
    """Обработчики группировки"""
    
    @staticmethod
    def register_handlers(dp):
        """Регистрация обработчиков группировки"""
        
        @dp.callback_query(F.data.in_(["enable_group_mode", "new_enable_group_mode"]))
        async def handle_enable_group_mode(callback: types.CallbackQuery, state: FSMContext):
            """Включить режим группировки"""
            await MoveStateManager.toggle_group_mode(state, enable=True)
            await BaseMoveHandlers.update_move_interface(callback, state)
            await callback.answer()
        
        @dp.callback_query(F.data.startswith(("move_select_button:", "new_move_select_button:")))
        async def handle_select_button(callback: types.CallbackQuery, state: FSMContext):
            """Выбор кнопки для группировки"""
            item_id = CallbackDataExtractor.extract_item_id(callback.data)
            
            data = await state.get_data()
            selected_buttons = data.get('selected_buttons', [])
            
            if item_id in selected_buttons:
                selected_buttons.remove(item_id)
                await callback.answer("❌ Кнопка убрана из выбора")
            else:
                selected_buttons.append(item_id)
                await callback.answer("✅ Кнопка добавлена в выбор")
            
            await state.update_data(selected_buttons=selected_buttons)
            await BaseMoveHandlers.update_move_interface(callback, state)
        
        @dp.callback_query(F.data.in_(["group_selected_buttons", "new_group_selected_buttons"]))
        async def handle_group_selected_buttons(callback: types.CallbackQuery, state: FSMContext):
            """Группировка выбранных кнопок"""
            data = await state.get_data()
            selected_buttons = data.get('selected_buttons', [])
            
            if len(selected_buttons) < 2:
                await callback.answer("❌ Выберите минимум 2 кнопки", show_alert=True)
                return
            
            if len(selected_buttons) > 2:
                await callback.answer("❌ Пока поддерживается группировка только 2 кнопок", show_alert=True)
                return
            
            item1_id, item2_id = selected_buttons[0], selected_buttons[1]
            
            # Получаем позиции кнопок для определения правильного порядка
            from ...database import get_menu_item
            item1 = get_menu_item(item1_id)
            item2 = get_menu_item(item2_id)
            
            if not item1 or not item2:
                await callback.answer("❌ Ошибка получения данных кнопок", show_alert=True)
                return
            
            # Проверяем, что кнопки находятся на одном уровне иерархии
            parent1 = item1[1]  # parent_id index
            parent2 = item2[1]  # parent_id index
            
            if parent1 != parent2:
                await callback.answer("❌ Кнопки должны находиться на одном уровне", show_alert=True)
                return
            
            # Группируем в порядке выбора: первая выбранная будет первой в группе
            # item1_id - первая выбранная, item2_id - вторая выбранная
            success = group_buttons(item1_id, item2_id)
            
            if success:
                await callback.answer("✅ Кнопки сгруппированы")
                await MoveStateManager.toggle_group_mode(state, enable=False)
                await BaseMoveHandlers.update_move_interface(callback, state)
            else:
                await callback.answer("❌ Не удалось сгруппировать кнопки", show_alert=True)
        
        @dp.callback_query(F.data.in_(["cancel_grouping", "new_cancel_grouping", "new_disable_group_mode"]))
        async def handle_cancel_grouping(callback: types.CallbackQuery, state: FSMContext):
            """Отмена режима группировки"""
            await MoveStateManager.toggle_group_mode(state, enable=False)
            await BaseMoveHandlers.update_move_interface(callback, state)
            await callback.answer("❌ Режим группировки отменен")
        
        @dp.callback_query(F.data.in_(["clear_selection", "new_clear_selection"]))
        async def handle_clear_selection(callback: types.CallbackQuery, state: FSMContext):
            """Очистить выбор кнопок в режиме группировки"""
            await MoveStateManager.clear_button_selection(state)
            await BaseMoveHandlers.update_move_interface(callback, state)
            await callback.answer("🚫 Выбор кнопок отменен")


class UngroupingHandlers:
    """Обработчики разгруппировки"""
    
    @staticmethod
    def register_handlers(dp):
        """Регистрация обработчиков разгруппировки"""
        
        @dp.callback_query(F.data == "new_ungroup_mode")
        async def handle_ungroup_mode(callback: types.CallbackQuery, state: FSMContext):
            """Переход в режим разделения групп"""
            data = await state.get_data()
            current_parent_id = data.get('current_parent_id')
            
            groups = get_button_groups(parent_id=current_parent_id)
            
            if not groups:
                await callback.answer(MSG_ERROR_NO_GROUPS, show_alert=True)
                return
            
            await safe_delete_message(callback.message)
            
            text = MessageTextBuilder.get_ungroup_mode_text()
            keyboard = build_ungroup_mode_keyboard(parent_id=current_parent_id)
            
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
        
        @dp.callback_query(F.data.startswith(("ungroup_button:", "new_ungroup_buttons:")))
        async def handle_ungroup_buttons(callback: types.CallbackQuery, state: FSMContext):
            """Запрос на разгруппировку кнопок"""
            group_position = CallbackDataExtractor.extract_group_position(callback.data)
            
            data = await state.get_data()
            current_parent_id = data.get('current_parent_id')
            
            groups = get_button_groups(parent_id=current_parent_id)
            group_items = None
            for pos, items in groups:
                if pos == group_position:
                    group_items = items
                    break
            
            if not group_items or len(group_items) < 2:
                await callback.answer("❌ Группа не найдена", show_alert=True)
                return
            
            group_titles = []
            for item_id in group_items:
                item = get_menu_item(item_id)
                if item:
                    group_titles.append(item[2])  # title is at index 2
            
            text = MessageTextBuilder.get_ungroup_confirmation_text(group_titles)
            keyboard = build_new_ungroup_keyboard(group_position)
            
            await safe_edit_message(callback.message, text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
        
        @dp.callback_query(F.data == "back_to_ungroup_mode")
        async def handle_back_to_ungroup_mode(callback: types.CallbackQuery, state: FSMContext):
            """Возврат к меню разделения групп"""
            await safe_delete_message(callback.message)
            
            data = await state.get_data()
            current_parent_id = data.get('current_parent_id')
            
            text = MessageTextBuilder.get_ungroup_mode_text()
            keyboard = build_ungroup_mode_keyboard(parent_id=current_parent_id)
            
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
        
        @dp.callback_query(F.data.startswith(("confirm_ungroup:", "new_confirm_ungroup:")))
        async def handle_confirm_ungroup(callback: types.CallbackQuery, state: FSMContext):
            """Подтверждение разгруппировки"""
            group_position = CallbackDataExtractor.extract_group_position(callback.data)
            data = await state.get_data()
            current_parent_id = data.get('current_parent_id')
            success = ungroup_buttons(group_position, parent_id=current_parent_id)
            
            if success:
                await callback.answer("✅ Группа разделена")
                await MoveStateManager.clear_selections(state)
                
                # Возврат к меню разделения
                await safe_delete_message(callback.message)
                text = MessageTextBuilder.get_ungroup_mode_text()
                keyboard = build_ungroup_mode_keyboard(parent_id=current_parent_id)
                await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await callback.answer("❌ Не удалось разделить группу", show_alert=True)
