"""Утилиты для работы с перемещением кнопок"""

from aiogram.fsm.context import FSMContext
from ...keyboards.move_keyboards import build_new_move_keyboard
from ...utils.texts import (
    MSG_MOVE_MODE_HEADER, MSG_MOVE_MODE_INSTRUCTIONS,
    MSG_GROUP_MODE_ACTIVE, MSG_GROUP_MODE_INSTRUCTIONS,
    MSG_FIRST_BUTTON_SELECTED, MSG_GROUP_READY,
    MSG_UNGROUP_MODE_ACTIVE, MSG_UNGROUP_MODE_INSTRUCTIONS
)
from ...database import get_menu_item


class MoveStateManager:
    """Менеджер состояния для режима перемещения"""
    
    @staticmethod
    async def init_move_state(state: FSMContext) -> None:
        """Инициализация состояния режима перемещения"""
        await state.update_data(
            selected_buttons=[],
            group_mode=False,
            editing_item_id=None,
            selected_item_id=None,
            selected_group_position=None,
            current_parent_id=None  # Добавляем текущий parent_id
        )
    
    @staticmethod
    async def clear_selections(state: FSMContext) -> None:
        """Очистка всех выделений"""
        await state.update_data(
            selected_item_id=None,
            selected_group_position=None
        )
    
    @staticmethod
    async def toggle_item_selection(state: FSMContext, item_id: int) -> None:
        """Переключение выделения элемента"""
        data = await state.get_data()
        current_selected = data.get('selected_item_id')
        
        if current_selected == item_id:
            await state.update_data(selected_item_id=None, selected_group_position=None)
        else:
            await state.update_data(selected_item_id=item_id, selected_group_position=None)
    
    @staticmethod
    async def toggle_group_selection(state: FSMContext, group_position: int) -> None:
        """Переключение выделения группы"""
        data = await state.get_data()
        current_selected = data.get('selected_group_position')
        
        if current_selected == group_position:
            await state.update_data(selected_group_position=None, selected_item_id=None)
        else:
            await state.update_data(selected_group_position=group_position, selected_item_id=None)
    
    @staticmethod
    async def toggle_group_mode(state: FSMContext, enable: bool = None) -> None:
        """Переключение режима группировки"""
        if enable is None:
            data = await state.get_data()
            enable = not data.get('group_mode', False)
        
        await state.update_data(
            group_mode=enable,
            selected_buttons=[] if enable else None,
            selected_item_id=None,
            selected_group_position=None
        )
    
    @staticmethod
    async def clear_button_selection(state: FSMContext) -> None:
        """Очистить выбор кнопок в режиме группировки, но остаться в режиме"""
        await state.update_data(selected_buttons=[])


class MoveKeyboardBuilder:
    """Строитель клавиатур для режима перемещения"""
    
    @staticmethod
    async def build_keyboard_with_state(state: FSMContext, **kwargs):
        """Построить клавиатуру с учетом текущего состояния"""
        data = await state.get_data()
        
        params = {
            'parent_id': data.get('current_parent_id'),  # Используем current_parent_id из состояния
            'selected_buttons': data.get('selected_buttons', []),
            'group_mode': data.get('group_mode', False),
            'editing_item_id': data.get('editing_item_id'),
            'selected_item_id': data.get('selected_item_id'),
            'selected_group_position': data.get('selected_group_position')
        }
        
        # Перезаписываем переданными параметрами
        params.update(kwargs)
        
        return build_new_move_keyboard(**params)


class MessageTextBuilder:
    """Строитель текстов сообщений"""
    
    @staticmethod
    def get_default_move_text() -> str:
        """Получить стандартный текст режима перемещения"""
        return MSG_MOVE_MODE_HEADER + MSG_MOVE_MODE_INSTRUCTIONS
    
    @staticmethod
    def get_group_mode_text(selected_buttons: list) -> str:
        """Получить текст для режима группировки в зависимости от количества выбранных кнопок"""
        selected_count = len(selected_buttons)
        
        if selected_count == 0:
            # Начальное состояние режима группировки
            return MSG_GROUP_MODE_ACTIVE + MSG_GROUP_MODE_INSTRUCTIONS
        
        elif selected_count == 1:
            # Выбрана первая кнопка
            item = get_menu_item(selected_buttons[0])
            button_name = item['title'] if item else f"ID {selected_buttons[0]}"
            return MSG_FIRST_BUTTON_SELECTED.format(button_name=button_name)
        
        elif selected_count == 2:
            # Выбраны две кнопки - готовы к группировке
            first_item = get_menu_item(selected_buttons[0])
            second_item = get_menu_item(selected_buttons[1])
            
            first_button = first_item['title'] if first_item else f"ID {selected_buttons[0]}"
            second_button = second_item['title'] if second_item else f"ID {selected_buttons[1]}"
            
            return MSG_GROUP_READY.format(first_button=first_button, second_button=second_button)
        
        else:
            # Более двух кнопок - не поддерживается
            return MSG_GROUP_MODE_ACTIVE + "❌ Поддерживается группировка только 2 кнопок"
    
    @staticmethod
    def get_ungroup_mode_text() -> str:
        """Получить текст для режима разгруппировки"""
        return MSG_UNGROUP_MODE_ACTIVE + MSG_UNGROUP_MODE_INSTRUCTIONS
    
    @staticmethod
    def get_ungroup_confirmation_text(group_titles: list) -> str:
        """Получить текст подтверждения разгруппировки"""
        titles_str = ' + '.join(group_titles[:2])
        return (
            f"🔓 <b>Разделение группы</b>\n\n"
            f"Группа: {titles_str}\n\n"
            f"Вы уверены, что хотите разделить эту группу?\n"
            f"Одна кнопка останется на текущей позиции, "
            f"другая переместится в конец списка."
        )


class CallbackDataExtractor:
    """Извлекатель данных из callback'ов"""
    
    @staticmethod
    def extract_item_id(callback_data: str) -> int:
        """Извлечь ID элемента из callback данных"""
        return int(callback_data.split(":")[1])
    
    @staticmethod
    def extract_group_position(callback_data: str) -> int:
        """Извлечь позицию группы из callback данных"""
        return int(callback_data.split(":")[1])
