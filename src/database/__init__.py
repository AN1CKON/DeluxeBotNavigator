"""
Модуль базы данных для DeluxeNavigateBot

Этот модуль предоставляет чистый и модульный интерфейс для работы с базой данных.
Все функции разделены по логическим группам для лучшей организации кода.

Модули:
- base: Базовые функции подключения и инициализации БД
- menu: Все функции для работы с меню (CRUD, запросы, утилиты, статистика)
- admins: Все функции для работы с администраторами (CRUD, запросы, управление, статистика)
- users: Управление пользователями
- positioning: Управление позиционированием элементов
"""
# Импорты из базового модуля
from .base import init_db, get_db

# Импорты модуля меню
from .menu import (
    add_menu_item,
    delete_menu_item,
    update_menu_item,
    clear_all_menu,
    get_menu_item_by_id,
    get_menu_item,
    get_all_menu_items,
    get_child_menu_items,
    get_menu_items,
    get_menu_items_with_positions,
    get_menu_items_grouped,
    has_children,
    change_menu_position,
    update_menu_item_image,
    check_menu_item_exists,
    get_menu_path,
    search_menu_items,
    get_menu_stats,
    get_menu_statistics
)

# Импорты модуля пользователей
from .users import (
    add_user,
    get_user,
    update_user_visit,
    set_welcome_shown,
    is_welcome_shown,
    get_all_users,
    get_users_count,
    delete_user,
    user_exists,
    update_user_info,
    get_users_statistics,
    is_new_user,
    register_user,
    mark_welcome_shown
)

# Импорты модуля администраторов
from .admins import (
    add_admin,
    remove_admin,
    update_admin_info,
    clear_all_admins,
    is_admin,
    is_super_admin,
    get_admin,
    get_admin_info,
    get_all_admins,
    get_admins_count,
    get_super_admins_count,
    get_admins_added_by,
    promote_to_super_admin,
    demote_from_super_admin,
    init_super_admin,
    get_admins_statistics
)

# Импорты модуля позиционирования
from .positioning import (
    move_button_up,
    move_button_down,
    group_buttons,
    ungroup_buttons,
    get_button_groups,
    get_ordered_items,
    move_group_up,
    move_group_down,
    can_move_up_new,
    can_move_down_new,
    get_next_position,
    is_item_in_group
)


__all__ = [
    # Базовые функции
    'init_db', 'get_db',
    
    # Функции меню
    'add_menu_item', 'delete_menu_item', 'get_menu_item_by_id', 
    'get_all_menu_items', 'get_child_menu_items', 'update_menu_item',
    'clear_all_menu', 'check_menu_item_exists', 'get_menu_path',
    'search_menu_items', 'get_menu_statistics', 'get_menu_items',
    'get_menu_items_with_positions', 'get_menu_items_grouped',
    'has_children', 'change_menu_position', 'update_menu_item_image',
    'get_menu_stats', 'get_menu_item',
    
    # Функции пользователей
    'add_user', 'get_user', 'update_user_visit', 'set_welcome_shown',
    'is_welcome_shown', 'get_all_users', 'get_users_count', 'delete_user',
    'user_exists', 'update_user_info', 'get_users_statistics',
    'is_new_user', 'register_user', 'mark_welcome_shown',
    
    # Функции администраторов
    'add_admin', 'remove_admin', 'is_admin', 'is_super_admin',
    'get_admin', 'get_admin_info', 'get_all_admins', 'get_admins_count',
    'get_super_admins_count', 'update_admin_info', 'promote_to_super_admin',
    'demote_from_super_admin', 'get_admins_added_by', 'clear_all_admins',
    'get_admins_statistics', 'init_super_admin'
    
    # Функции позиционирования
    'move_button_up', 'move_button_down', 'get_next_position',
    'group_buttons', 'ungroup_buttons', 'get_button_groups', 'get_ordered_items',
    'move_group_up', 'move_group_down', 'can_move_up_new', 'can_move_down_new',
    'is_item_in_group'
]
