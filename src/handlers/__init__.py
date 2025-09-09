from .user_interface import (
    register_start,
    register_navigation, 
    register_welcome
)
from .admin_manager import (
    register_admin_manage
)
from .admin_menu import (
    register_admin_menu,
    register_admin_add,
    register_admin_edit,
    register_admin_delete,
    register_admin_clear,
    register_admin_cancel,
    register_stats_handlers
)
from .edit_actions import register_edit_actions

def register_handlers(dp, bot):
    # Порядок регистрации важен - сначала специфичные, потом общие
    register_start(dp)
    register_navigation(dp)
    register_welcome(dp)
    register_admin_menu(dp, bot)  # Переименовано из admin_panel
    register_admin_add(dp)
    register_admin_edit(dp)
    register_admin_delete(dp)
    register_admin_clear(dp, bot)
    register_admin_manage(dp, bot)  # Обработчик управления админами
    register_edit_actions(dp)  # Обработчики действий редактирования
    register_stats_handlers(dp)  # Обработчики управления статистикой
    register_admin_cancel(dp)  # Должен быть последним для перехвата всех admin_cancel

    
