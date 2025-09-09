"""
Операции перемещения кнопок и групп.
"""

import logging
from typing import Optional
from .helpers import get_item_info, get_items_at_position, get_adjacent_position, update_positions

logger = logging.getLogger(__name__)


def move_button_up(item_id: int) -> bool:
    """
    Перемещает кнопку вверх на одну позицию.
    Если предыдущая позиция содержит группу, сдвигает всю группу вниз.
    Если предыдущая позиция содержит одиночную кнопку, меняет местами.

    Args:
        item_id: ID кнопки для перемещения

    Returns:
        True если операция успешна, False иначе
    """
    item_info = get_item_info(item_id)
    if not item_info:
        logger.warning(f"⚠️ Кнопка с ID {item_id} не найдена")
        return False

    current_position, parent_id = item_info

    # Проверяем, что текущая кнопка не в группе
    current_items = get_items_at_position(current_position, parent_id)
    if len(current_items) > 1:
        logger.warning(f"⚠️ Нельзя перемещать кнопку {item_id} - она находится в группе")
        return False

    # Находим предыдущую позицию
    prev_position = get_adjacent_position(current_position, 'up', parent_id)
    if prev_position is None:
        logger.info(f"ℹ️ Кнопка {item_id} уже находится в самом верху")
        return False

    # Проверяем, сколько элементов в предыдущей позиции
    prev_items = get_items_at_position(prev_position, parent_id)

    if len(prev_items) == 1:
        # Предыдущая позиция содержит одиночную кнопку - просто меняем местами
        prev_item_id = prev_items[0]
        updates = [
            (item_id, prev_position),
            (prev_item_id, current_position)
        ]
        update_positions(updates, parent_id)
        logger.info(f"⬆️ Кнопка {item_id} перемещена вверх (позиция {current_position} -> {prev_position})")
        return True

    elif len(prev_items) > 1:
        # Предыдущая позиция содержит группу - сдвигаем всю группу на текущую позицию
        updates = [(item_id, prev_position)] + [(item, current_position) for item in prev_items]
        update_positions(updates, parent_id)
        logger.info(f"⬆️ Кнопка {item_id} перемещена вверх, группа сдвинута (позиция {current_position} -> {prev_position})")
        return True

    return False


def move_button_down(item_id: int) -> bool:
    """
    Перемещает кнопку вниз на одну позицию.
    Если следующая позиция содержит группу, сдвигает всю группу вверх.
    Если следующая позиция содержит одиночную кнопку, меняет местами.

    Args:
        item_id: ID кнопки для перемещения

    Returns:
        True если операция успешна, False иначе
    """
    item_info = get_item_info(item_id)
    if not item_info:
        logger.warning(f"⚠️ Кнопка с ID {item_id} не найдена")
        return False

    current_position, parent_id = item_info

    # Проверяем, что текущая кнопка не в группе
    current_items = get_items_at_position(current_position, parent_id)
    if len(current_items) > 1:
        logger.warning(f"⚠️ Нельзя перемещать кнопку {item_id} - она находится в группе")
        return False

    # Находим следующую позицию
    next_position = get_adjacent_position(current_position, 'down', parent_id)
    if next_position is None:
        logger.info(f"ℹ️ Кнопка {item_id} уже находится в самом низу")
        return False

    # Проверяем, сколько элементов в следующей позиции
    next_items = get_items_at_position(next_position, parent_id)

    if len(next_items) == 1:
        # Следующая позиция содержит одиночную кнопку - просто меняем местами
        next_item_id = next_items[0]
        updates = [
            (item_id, next_position),
            (next_item_id, current_position)
        ]
        update_positions(updates, parent_id)
        logger.info(f"⬇️ Кнопка {item_id} перемещена вниз (позиция {current_position} -> {next_position})")
        return True

    elif len(next_items) > 1:
        # Следующая позиция содержит группу - сдвигаем всю группу на текущую позицию
        updates = [(item_id, next_position)] + [(item, current_position) for item in next_items]
        update_positions(updates, parent_id)
        logger.info(f"⬇️ Кнопка {item_id} перемещена вниз, группа сдвинута (позиция {current_position} -> {next_position})")
        return True

    return False


def move_group_up(group_position: int, parent_id: Optional[int] = None) -> Optional[int]:
    """
    Перемещает всю группу кнопок вверх.

    Args:
        group_position: Позиция группы для перемещения
        parent_id: ID родительского элемента

    Returns:
        Новая позиция группы если операция успешна, None иначе
    """
    # Находим предыдущую позицию
    prev_position = get_adjacent_position(group_position, 'up', parent_id)
    if prev_position is None:
        logger.info(f"ℹ️ Группа на позиции {group_position} уже находится в самом верху")
        return None

    # Получаем элементы обеих позиций
    group_items = get_items_at_position(group_position, parent_id)
    prev_items = get_items_at_position(prev_position, parent_id)

    # Меняем местами все элементы
    updates = []
    # Временно помечаем элементы текущей группы отрицательными позициями
    for item in group_items:
        updates.append((item, -group_position))

    # Перемещаем элементы с предыдущей позиции на текущую
    for item in prev_items:
        updates.append((item, group_position))

    # Перемещаем отмеченные элементы на предыдущую позицию
    for item in group_items:
        updates.append((item, prev_position))

    update_positions(updates, parent_id)
    logger.info(f"⬆️ Группа перемещена вверх (позиция {group_position} ⟷ {prev_position})")
    return prev_position


def move_group_down(group_position: int, parent_id: Optional[int] = None) -> Optional[int]:
    """
    Перемещает всю группу кнопок вниз.

    Args:
        group_position: Позиция группы для перемещения
        parent_id: ID родительского элемента

    Returns:
        Новая позиция группы если операция успешна, None иначе
    """
    # Находим следующую позицию
    next_position = get_adjacent_position(group_position, 'down', parent_id)
    if next_position is None:
        logger.info(f"ℹ️ Группа на позиции {group_position} уже находится в самом низу")
        return None

    # Получаем элементы обеих позиций
    group_items = get_items_at_position(group_position, parent_id)
    next_items = get_items_at_position(next_position, parent_id)

    # Меняем местами все элементы
    updates = []
    # Временно помечаем элементы текущей группы отрицательными позициями
    for item in group_items:
        updates.append((item, -group_position))

    # Перемещаем элементы со следующей позиции на текущую
    for item in next_items:
        updates.append((item, group_position))

    # Перемещаем отмеченные элементы на следующую позицию
    for item in group_items:
        updates.append((item, next_position))

    update_positions(updates, parent_id)
    logger.info(f"⬇️ Группа перемещена вниз (позиция {group_position} ⟷ {next_position})")
    return next_position