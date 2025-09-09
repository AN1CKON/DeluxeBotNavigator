"""
Рефакторенный обработчик перемещения кнопок

Этот модуль обеспечивает чистую архитектуру для управления перемещением,
группировкой и разгруппировкой кнопок в боте DeluxeNavigator.

Ключевые принципы рефакторинга:
- Разделение ответственности
- Устранение дублирования кода
- Централизация управления состоянием
- Модульная архитектура
"""

from .move_handlers import NavigationHandlers, MovementHandlers, ControlHandlers
from .move_grouping import GroupingHandlers, UngroupingHandlers
from .move_utils import MoveStateManager, MessageTextBuilder


# Экспорт основных функций для обратной совместимости
async def show_move_menu(message, state):
    """Показать меню режима перемещения кнопок"""
    from .move_handlers import BaseMoveHandlers
    await BaseMoveHandlers.show_move_menu(message, state)


def get_move_menu_text():
    """Получить стандартный текст для меню перемещения"""
    return MessageTextBuilder.get_default_move_text()


def register_move_action(dp):
    """
    Регистрация всех обработчиков для перемещения кнопок
    
    Регистрирует:
    - Обработчики навигации (переходы между режимами)
    - Обработчики перемещения (вверх/вниз для кнопок и групп)
    - Обработчики управления (показ/скрытие контролов)
    - Обработчики группировки (создание групп)
    - Обработчики разгруппировки (разделение групп)
    """
    # Регистрируем все категории обработчиков
    NavigationHandlers.register_handlers(dp)
    MovementHandlers.register_handlers(dp)
    ControlHandlers.register_handlers(dp)
    GroupingHandlers.register_handlers(dp)
    UngroupingHandlers.register_handlers(dp)

