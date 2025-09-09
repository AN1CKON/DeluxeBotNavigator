"""
Операции группировки и разгруппировки кнопок.
"""

import logging
import datetime
from typing import Optional
from .helpers import get_item_info, get_max_position, update_positions

logger = logging.getLogger(__name__)


def group_buttons(item1_id: int, item2_id: int) -> bool:
    """
    Группирует две кнопки. Общий position = наименьший из двух.
    Остальные кнопки с position больше максимального сдвигаются на -1.

    Args:
        item1_id: ID первой кнопки
        item2_id: ID второй кнопки

    Returns:
        True если операция успешна, False иначе
    """
    item1_info = get_item_info(item1_id)
    item2_info = get_item_info(item2_id)

    if not item1_info or not item2_info:
        logger.warning("⚠️ Одна из кнопок не найдена")
        return False

    pos1, parent1 = item1_info
    pos2, parent2 = item2_info

    # Проверяем, что кнопки в одной группе
    if parent1 != parent2:
        logger.warning("⚠️ Кнопки должны быть в одной группе для группировки")
        return False

    # Определяем общий position (наименьший) и какую позицию нужно освободить
    group_position = min(pos1, pos2)
    position_to_remove = max(pos1, pos2)

    # Присваиваем обеим кнопкам одинаковую позицию (наименьшую)
    # Обновляем timestamp для сохранения порядка выбора
    current_time = datetime.datetime.now()

    # Первая выбранная кнопка получает более ранний timestamp
    first_timestamp = current_time - datetime.timedelta(seconds=1)
    updates = [
        (item1_id, group_position, first_timestamp),
        (item2_id, group_position, current_time)
    ]

    # Сдвигаем все кнопки, которые идут после освобождаемой позиции, на -1
    # Это нужно сделать отдельно, так как требует более сложной логики
    from ..base import get_db
    with get_db() as conn:
        c = conn.cursor()

        # Обновляем позиции группируемых элементов
        c.execute("UPDATE menu SET position = ?, updated_at = ? WHERE id = ?",
                 (group_position, first_timestamp, item1_id))
        c.execute("UPDATE menu SET position = ?, updated_at = ? WHERE id = ?",
                 (group_position, current_time, item2_id))

        # Сдвигаем остальные элементы
        if parent1 is None:
            c.execute("""
                UPDATE menu SET position = position - 1
                WHERE parent_id IS NULL AND position > ? AND id NOT IN (?, ?)
            """, (position_to_remove, item1_id, item2_id))
        else:
            c.execute("""
                UPDATE menu SET position = position - 1
                WHERE parent_id = ? AND position > ? AND id NOT IN (?, ?)
            """, (parent1, position_to_remove, item1_id, item2_id))

        conn.commit()

    logger.info(f"🔗 Кнопки {item1_id} и {item2_id} сгруппированы (позиция {group_position})")
    return True


def ungroup_buttons(group_position: int, parent_id: Optional[int] = None) -> bool:
    """
    Разделяет группу кнопок. Первая кнопка остается с тем же position,
    вторая получает максимальный position + 1.

    Args:
        group_position: Позиция группы для разделения
        parent_id: ID родительского элемента

    Returns:
        True если операция успешна, False иначе
    """
    from .helpers import get_items_at_position

    # Находим все кнопки в группе
    group_items = get_items_at_position(group_position, parent_id)

    if len(group_items) < 2:
        logger.warning(f"⚠️ В позиции {group_position} нет группы для разделения")
        return False

    if len(group_items) > 2:
        logger.warning(f"⚠️ В позиции {group_position} больше 2 кнопок - неподдерживаемая ситуация")
        return False

    first_item_id = group_items[0]
    second_item_id = group_items[1]

    # Первая кнопка остается с тем же position
    # Для второй кнопки находим максимальную позицию и добавляем +1
    max_pos = get_max_position(parent_id)
    new_position = max_pos + 1

    # Обновляем позицию второй кнопки
    updates = [(second_item_id, new_position)]
    update_positions(updates, parent_id)

    logger.info(f"🔓 Группа в позиции {group_position} разделена: кнопка {first_item_id} остается на {group_position}, кнопка {second_item_id} перемещена на {new_position}")
    return True