"""Init файл для действий редактирования"""

from .rename_action import register_rename_action
from .style_action import register_style_action
from .image_action import register_image_action
from .move_action import register_move_action

def register_edit_actions(dp):
    """Централизованная регистрация всех обработчиков действий редактирования"""
    register_rename_action(dp)
    register_style_action(dp)
    register_image_action(dp)
    register_move_action(dp)
