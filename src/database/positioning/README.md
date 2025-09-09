# Модуль позиционирования элементов меню

Этот модуль предоставляет функциональность для управления позициями и группировкой элементов меню в базе данных.

## Структура модулей

### `core.py`
Основной модуль с классом `PositioningManager` для объектно-ориентированного интерфейса и обратной совместимости.

### `position_utils.py`
Утилиты для работы с позициями:
- `get_next_position()` - получение следующей позиции
- `get_button_groups()` - получение списка групп
- `get_ordered_items()` - получение упорядоченного списка элементов

### `move_operations.py`
Операции перемещения:
- `move_button_up()` / `move_button_down()` - перемещение одиночных кнопок
- `move_group_up()` / `move_group_down()` - перемещение групп

### `group_operations.py`
Операции группировки:
- `group_buttons()` - группировка двух кнопок
- `ungroup_buttons()` - разгруппировка группы

### `validation.py`
Функции валидации:
- `can_move_up_new()` / `can_move_down_new()` - проверка возможности перемещения
- `is_item_in_group()` - проверка принадлежности к группе

### `helpers.py`
Вспомогательные функции для внутреннего использования:
- `get_item_info()` - получение информации об элементе
- `get_items_at_position()` - получение элементов на позиции
- `get_max_position()` - получение максимальной позиции
- `get_adjacent_position()` - получение соседней позиции
- `update_positions()` - пакетное обновление позиций

## Использование

```python
from src.database.positioning import PositioningManager

# Использование менеджера
manager = PositioningManager(parent_id=None)
next_pos = manager.get_next_position()
success = manager.move_up(item_id=1)

# Или прямой импорт функций
from src.database.positioning import move_button_up, group_buttons
move_button_up(1)
group_buttons(1, 2)
```

## Особенности

- Поддержка иерархических меню через `parent_id`
- Группировка элементов с сохранением порядка
- Автоматическое управление позициями при перемещениях
- Подробное логирование операций
- Типизированные интерфейсы
