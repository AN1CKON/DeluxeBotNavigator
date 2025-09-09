from aiogram.fsm.state import State, StatesGroup

class MenuState(StatesGroup):
    waiting_for_parent = State()
    waiting_for_title = State()
    waiting_for_content_type = State()
    waiting_for_image = State()  # Новое состояние для добавления изображения
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
    # Состояния для перемещения кнопок
    move_mode = State()
    group_mode = State()
    waiting_for_first_button = State()
    waiting_for_second_button = State()
    group_ready_to_lock = State()

class ReviewStates(StatesGroup):
    """Состояния для формы отзыва"""
    waiting_for_review_content = State()

class AdminStates(StatesGroup):
    """Состояния для управления администраторами"""
    waiting_for_new_admin_id = State()
    waiting_for_remove_admin_id = State()
    
    # Состояния для управления статистикой плагинов
    managing_plugin_stats = State()
    waiting_for_plugin_name = State()
    waiting_for_plugin_status = State()
    waiting_for_plugin_progress = State()
    editing_plugin_stat = State()
    editing_plugin_mode = State()
    waiting_for_edit_plugin_name = State()
