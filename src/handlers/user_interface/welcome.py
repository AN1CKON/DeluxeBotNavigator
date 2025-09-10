"""Обработчик приветствия новых пользователей"""

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from src.models import WelcomeState
from src.keyboards.keyboards import welcome_keyboard, welcome_mobile_keyboard
from src.handlers.common.utils import safe_delete_message, show_main_menu_for_callback
from src.database import mark_welcome_shown
from src.config.config import get_video_path
from src.utils.texts import WELCOME_MESSAGE, WELCOME_MESSAGE_MOBILE

# Константы для сообщений об ошибках
VIDEO_UNAVAILABLE_MSG = "📺 Видео-инструкция временно недоступна\n\n{}"
MOBILE_VIDEO_UNAVAILABLE_MSG = "📱 <b>Инструкция для мобильных устройств</b>\n\n📺 Видео-инструкция временно недоступна\n\n{}"
PC_VIDEO_UNAVAILABLE_MSG = "🖥️ <b>Инструкция для ПК</b>\n\n📺 Видео-инструкция временно недоступна\n\n{}"


async def _send_video_message(message: types.Message, video_filename: str, caption: str, keyboard):
    """Отправляет видео сообщение с обработкой ошибок"""
    try:
        video_path = get_video_path(video_filename)
        video = FSInputFile(video_path)
        
        await message.answer_video(
            video,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return True
    except Exception:
        # Если видео недоступно, показываем только текст
        await message.answer(
            VIDEO_UNAVAILABLE_MSG.format(caption),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return False


async def _edit_video_message(callback: types.CallbackQuery, video_filename: str, 
                            caption: str, keyboard, fallback_msg: str):
    """Редактирует сообщение с видео и обрабатывает ошибки"""
    try:
        video_path = get_video_path(video_filename)
        video = FSInputFile(video_path)
        
        await callback.message.edit_media(
            media=types.InputMediaVideo(
                media=video,
                caption=caption,
                parse_mode="HTML"
            ),
            reply_markup=keyboard
        )
        return True
    except Exception:
        # Если видео недоступно, показываем только текст
        await callback.message.edit_text(
            fallback_msg.format(caption),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return False


def register_welcome(dp):
    """Регистрирует обработчики приветствия"""
    
    async def show_welcome_message(message: types.Message, state: FSMContext):
        """Показывает приветственное сообщение с видеоинструкцией"""
        await _send_video_message(message, "setup_pc.mp4", WELCOME_MESSAGE, welcome_keyboard())
        await state.set_state(WelcomeState.showing_welcome)
    
    @dp.callback_query(F.data == "welcome_done")
    async def welcome_done_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработка нажатия кнопки 'Готово'"""
        # Отмечаем, что приветствие показано
        mark_welcome_shown(callback.from_user.id)
        
        # Удаляем приветственное сообщение и очищаем состояние
        await safe_delete_message(callback.message)
        await state.clear()
        
        # Показываем главное меню
        await show_main_menu_for_callback(callback)
        await callback.answer("✅ Добро пожаловать! Теперь вы можете пользоваться ботом.")
    
    @dp.callback_query(F.data == "welcome_mobile")
    async def welcome_mobile_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработка нажатия кнопки 'А если я с телефона?'"""
        await _edit_video_message(
            callback, 
            "setup_mobile.mp4", 
            WELCOME_MESSAGE_MOBILE, 
            welcome_mobile_keyboard(),
            MOBILE_VIDEO_UNAVAILABLE_MSG
        )
        await callback.answer("📱 Переключено на мобильную версию")
    
    @dp.callback_query(F.data == "welcome_pc")
    async def welcome_pc_callback(callback: types.CallbackQuery, state: FSMContext):
        """Обработка нажатия кнопки 'А если я с ПК?'"""
        await _edit_video_message(
            callback,
            "setup_pc.mp4",
            WELCOME_MESSAGE,
            welcome_keyboard(),
            PC_VIDEO_UNAVAILABLE_MSG
        )
        await callback.answer("🖥️ Переключено на версию для ПК")
    
    # Экспортируем функцию для использования в start.py
    return show_welcome_message
