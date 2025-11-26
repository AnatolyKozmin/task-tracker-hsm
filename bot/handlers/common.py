import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Действие отменено.\n\n"
        "📋 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()

