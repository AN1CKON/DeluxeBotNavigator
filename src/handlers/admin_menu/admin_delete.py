"""Обработчик удаления пунктов меню"""

from aiogram import types, F
from aiogram.types import FSInputFile
from src.database import delete_menu_item, get_menu_items, has_children, get_menu_item
from src.handlers.common.utils import safe_delete_message, send_notification_and_cleanup
from src.keyboards.keyboards_admin import delete_menu_keyboard, confirm_keyboard, admin_keyboard
from src.config.config import get_image_path
from src.utils.texts import *

def register_admin_delete(dp):
    async def notify_and_return_to_panel(message, text):
        """Уведомляет об успехе и возвращает в админ-панель"""
        await send_notification_and_cleanup(message, text)
        photo = FSInputFile(get_image_path("admin.JPG"))
        await message.answer_photo(photo, caption=ADMIN_PANEL_TITLE, reply_markup=admin_keyboard())

    def recursive_delete(item_id):
        """Рекурсивно удаляет элемент и всех его потомков"""
        children = get_menu_items(item_id)
        for child_id, _ in children:
            recursive_delete(child_id)
        delete_menu_item(item_id)

    @dp.callback_query(F.data == "admin_delete")
    async def admin_delete_start(callback: types.CallbackQuery):
        """Начало процесса удаления"""
        await safe_delete_message(callback.message)
        await callback.message.answer(MSG_CHOOSE_DELETE_SECTION, reply_markup=delete_menu_keyboard())

    @dp.callback_query(F.data.startswith("delete_parent:"))
    async def delete_parent_select(callback: types.CallbackQuery):
        """Выбор родительского элемента для удаления"""
        parent_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        
        if has_children(parent_id):
            # Если есть дочерние элементы, показываем их
            kb = delete_menu_keyboard(parent_id)
            await callback.message.answer(MSG_CHOOSE_DELETE_CHILD, reply_markup=kb)
        else:
            # Если нет дочерних элементов, запрашиваем подтверждение
            kb = confirm_keyboard(
                confirm_callback=f"confirm_delete:{parent_id}",
                back_callback="delete_parent_back"
            )
            await callback.message.answer(MSG_CONFIRM_DELETE_ITEM, reply_markup=kb)

    @dp.callback_query(F.data == "delete_parent_back")
    async def delete_parent_back(callback: types.CallbackQuery):
        """Возврат к выбору раздела для удаления"""
        await safe_delete_message(callback.message)
        await callback.message.answer(MSG_CHOOSE_DELETE_SECTION, reply_markup=delete_menu_keyboard())

    @dp.callback_query(F.data.startswith("delete_section:"))
    async def delete_section_confirm(callback: types.CallbackQuery):
        """Подтверждение удаления целого раздела"""
        section_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        kb = confirm_keyboard(
            confirm_callback=f"confirm_delete_section:{section_id}",
            back_callback=f"delete_parent:{section_id}",
            confirm_text=BUTTON_CONFIRM_DELETE_SECTION
        )
        await callback.message.answer(MSG_CONFIRM_DELETE_SECTION, reply_markup=kb)

    @dp.callback_query(F.data.startswith("confirm_delete:"))
    async def confirm_delete_item(callback: types.CallbackQuery):
        """Подтверждение удаления отдельного элемента"""
        item_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        delete_menu_item(item_id)
        await notify_and_return_to_panel(callback.message, MSG_ITEM_DELETED)

    @dp.callback_query(F.data.startswith("confirm_delete_section:"))
    async def confirm_delete_section(callback: types.CallbackQuery):
        """Подтверждение удаления целого раздела"""
        section_id = int(callback.data.split(":")[1])
        await safe_delete_message(callback.message)
        recursive_delete(section_id)
        await notify_and_return_to_panel(callback.message, MSG_SECTION_DELETED)
