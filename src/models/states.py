from aiogram.fsm.state import State, StatesGroup

class MenuState(StatesGroup):
    waiting_for_parent = State()
    waiting_for_title = State()
    waiting_for_content_type = State()
    waiting_for_content = State()
    # Для редактирования
    waiting_for_edit_item = State()
    waiting_for_edit_title = State()
    waiting_for_edit_content_type = State()
    waiting_for_edit_content = State()
    # Новые состояния для действий редактирования
    waiting_for_rename_title = State()
    waiting_for_style_type = State()
    waiting_for_style_content = State()
    # Состояния для изображений
    waiting_for_image_upload = State()
    waiting_for_image_action = State()

class WelcomeState(StatesGroup):
    """Состояния для приветствия новых пользователей"""
    showing_welcome = State()
