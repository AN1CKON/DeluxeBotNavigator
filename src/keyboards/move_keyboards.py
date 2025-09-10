"""Новые клавиатуры для режима перемещения с новым алгоритмом"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.database.positioning.core import get_ordered_items, get_button_groups, can_move_up_new, can_move_down_new
from src.database import has_children, get_menu_item
from src.utils.texts import *

def build_new_move_keyboard(parent_id=None, selected_buttons=None, group_mode=False, editing_item_id=None, selected_item_id=None, selected_group_position=None) -> InlineKeyboardMarkup:
    """
    Новая клавиатура для режима перемещения с улучшенным алгоритмом
    
    Args:
        parent_id: ID родительского элемента (None для корня)
        selected_buttons: Список выбранных кнопок для группировки
        group_mode: Активен ли режим группировки
        editing_item_id: ID редактируемого элемента
        selected_item_id: ID выбранного элемента для показа кнопок перемещения
        selected_group_position: Позиция выбранной группы для показа кнопок перемещения
    """
    kb = []
    
    if selected_buttons is None:
        selected_buttons = []
    
    # Получаем упорядоченный список элементов
    items = get_ordered_items(parent_id)
    
    # Получаем информацию о группах
    groups = get_button_groups(parent_id)
    group_positions = {pos: item_ids for pos, item_ids in groups}
    
    # Кнопка "Назад" если мы в папке
    if parent_id is not None:
        parent_item = get_menu_item(parent_id)
        if parent_item:
            parent_title = parent_item[2]  # title
            kb.append([InlineKeyboardButton(
                text=f"⬅️ Назад к '{parent_title}'",
                callback_data=f"move_back_to_parent:{parent_id}"
            )])
        kb.append([])  # Разделитель
    
    # Отображаем элементы
    current_position = None
    for item in items:
        item_id = item['id']
        title = item['title']
        position = item['position']
        is_grouped = item['is_grouped']
        
        # Если это начало новой позиции
        if current_position != position:
            current_position = position
            
            if is_grouped:
                # В режиме группировки не показываем группы
                if group_mode:
                    continue
                    
                # Отображаем группу
                group_items = group_positions.get(position, [])
                if len(group_items) >= 2:
                    group_titles = []
                    for group_item_id in group_items:
                        group_item = next((it for it in items if it['id'] == group_item_id), None)
                        if group_item:
                            group_titles.append(group_item['title'])
                    
                    # Сортируем названия по алфавиту в обратном порядке для консистентного отображения
                    group_title = f"🔗 {' + '.join(group_titles[:2])}"  # Показываем только первые 2
                    
                    # Добавляем индикатор выбранной группы
                    if selected_group_position == position:
                        group_title = f"{group_title} {SELECTED_INDICATOR}"  # Используем оранжевый ромб
                    
                    kb.append([InlineKeyboardButton(
                        text=group_title,
                        callback_data=f"new_move_show_group_controls:{position}"
                    )])
                    
                    # Кнопки перемещения для выбранной группы
                    if not group_mode and selected_group_position == position:
                        move_buttons = []
                        
                        # Проверяем возможность перемещения группы
                        first_item_id = group_items[0]  # Берем первый элемент группы для проверки
                        
                        if can_move_down_new(first_item_id):
                            move_buttons.append(InlineKeyboardButton(
                                text=BUTTON_MOVE_DOWN, 
                                callback_data=f"new_move_group_down:{position}"
                            ))
                        
                        if can_move_up_new(first_item_id):
                            move_buttons.append(InlineKeyboardButton(
                                text=BUTTON_MOVE_UP, 
                                callback_data=f"new_move_group_up:{position}"
                            ))
                        
                        # Убираем кнопку разгруппировки из контекстного меню группы
                        # Разгруппировка теперь доступна через отдельное меню
                        
                        # Добавляем кнопки перемещения группы в отдельный ряд (если есть)
                        if move_buttons:
                            if len(move_buttons) <= 2:
                                kb.append(move_buttons)
                            else:
                                # Разбиваем на две строки если кнопок много
                                kb.append(move_buttons[:2])
                                kb.append(move_buttons[2:])
            else:
                # Отображаем одиночный элемент
                display_title = title
                
                # Добавляем индикаторы выбора
                if item_id in selected_buttons:
                    if group_mode:
                        display_title = f"{title} {SELECTED_INDICATOR}"  # Оранжевый ромб справа от текста
                    else:
                        display_title = f"{title} ✅"
                elif selected_item_id == item_id:
                    display_title = f"{title} {SELECTED_INDICATOR}"  # Используем тот же индикатор для выбранных в обычном режиме
                
                # Добавляем индикатор если это дочерний элемент
                if has_children(item_id):
                    display_title = f"📁 {display_title}"
                
                # Определяем callback_data
                if group_mode:
                    callback_data = f"new_move_select_button:{item_id}"
                else:
                    callback_data = f"new_move_show_controls:{item_id}"
                
                kb.append([InlineKeyboardButton(
                    text=display_title,
                    callback_data=callback_data
                )])
                
                # Кнопки перемещения для выбранного элемента
                if not group_mode and selected_item_id == item_id:
                    # Собираем все кнопки управления в один ряд
                    control_buttons = []
                    
                    if can_move_down_new(item_id):
                        control_buttons.append(InlineKeyboardButton(
                            text=BUTTON_MOVE_DOWN, 
                            callback_data=f"new_move_down:{item_id}"
                        ))
                    
                    if can_move_up_new(item_id):
                        control_buttons.append(InlineKeyboardButton(
                            text=BUTTON_MOVE_UP, 
                            callback_data=f"new_move_up:{item_id}"
                        ))
                    
                    # Добавляем кнопку "Войти в папку" в тот же ряд
                    if has_children(item_id):
                        control_buttons.append(InlineKeyboardButton(
                            text="📂 Войти",
                            callback_data=f"move_enter_folder:{item_id}"
                        ))
                    
                    # Добавляем собранные кнопки в один ряд (если есть)
                    if control_buttons:
                        kb.append(control_buttons)
    
    # Убираем разделитель - он не нужен
    
    # Управляющие кнопки
    if group_mode:
        # Режим группировки
        control_buttons = []
        
        # Кнопка группировки появляется только после выбора двух кнопок
        if len(selected_buttons) >= 2:
            control_buttons.append(InlineKeyboardButton(
                text=BUTTON_LOCK_GROUP,
                callback_data="new_group_selected_buttons"
            ))
        
        # Кнопка "отменить выбор" появляется при выборе одной или более кнопок
        if len(selected_buttons) >= 1:
            control_buttons.append(InlineKeyboardButton(
                text=BUTTON_GROUP_CLEAR_SELECTION,
                callback_data="new_clear_selection"  # Очищаем выбор
            ))
        
        # Размещаем кнопки управления (замочек и отмена выбора) если есть
        if control_buttons:
            kb.append(control_buttons)
        
        # Кнопка "назад" всегда в самом низу, но только если не выбраны кнопки
        if len(selected_buttons) == 0:
            kb.append([InlineKeyboardButton(
                text=BUTTON_GROUP_MODE_EXIT,
                callback_data="new_disable_group_mode"  # Выходим из режима группировки (назад)
            )])
    else:
        # Обычный режим - добавляем кнопки группировки и разделения
        kb.append([
            InlineKeyboardButton(text=BUTTON_GROUP_MODE, callback_data="new_enable_group_mode"),
            InlineKeyboardButton(text=BUTTON_UNGROUP_MODE, callback_data="new_ungroup_mode")
        ])
        
        # Кнопка сохранения (возврата) только в обычном режиме
        kb.append([InlineKeyboardButton(
            text=BUTTON_SAVE,
            callback_data="admin_panel"  # Возвращаемся в главное меню админ-панели
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)


def build_new_ungroup_keyboard(group_position: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для подтверждения разгруппировки
    
    Args:
        group_position: Позиция группы для разгруппировки
    """
    kb = [
        [
            InlineKeyboardButton(
                text="✅ Да, разделить",
                callback_data=f"new_confirm_ungroup:{group_position}"
            ),
            InlineKeyboardButton(
                text="❌ Нет, оставить",
                callback_data="back_to_ungroup_mode"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=kb)


def build_ungroup_mode_keyboard(parent_id=None) -> InlineKeyboardMarkup:
    """
    Клавиатура для режима разделения групп
    Показывает все доступные для разделения группы
    
    Args:
        parent_id: ID родительского элемента (None для корня)
    """
    kb = []
    
    # Получаем информацию о группах
    groups = get_button_groups(parent_id)
    items = get_ordered_items(parent_id)
    
    if groups:
        for position, item_ids in groups:
            if len(item_ids) >= 2:
                # Получаем названия кнопок в группе
                group_titles = []
                for item_id in item_ids:
                    item = next((it for it in items if it['id'] == item_id), None)
                    if item:
                        group_titles.append(item['title'])
                
                group_title = f"🔗 {' + '.join(group_titles[:2])}"  # Показываем только первые 2
                if len(group_titles) > 2:
                    group_title += f" (+{len(group_titles) - 2})"
                
                kb.append([InlineKeyboardButton(
                    text=group_title,
                    callback_data=f"new_ungroup_buttons:{position}"
                )])
    
    if not kb:
        # Если нет групп для разделения
        kb.append([InlineKeyboardButton(
            text="ℹ️ Нет групп для разделения",
            callback_data="ignore"
        )])
    
    # Кнопка возврата
    kb.append([InlineKeyboardButton(
        text=BUTTON_EXIT,
        callback_data="new_move_mode"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)
