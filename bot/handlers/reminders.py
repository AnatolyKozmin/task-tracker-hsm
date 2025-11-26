import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.connection import get_db_manager
from database.repositories import ProjectRepository
from database.models import RoleType
from bot.keyboards import (
    get_reminders_settings_keyboard,
    get_reminder_time_keyboard,
    get_reminder_days_keyboard,
    get_cancel_keyboard,
)
from bot.states import ReminderStates

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":reminders"))
async def callback_reminders_settings(callback: CallbackQuery):
    """Настройки напоминаний проекта"""
    project_id = int(callback.data.split(":")[1])
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        
        if not project:
            await callback.answer("❌ Проект не найден", show_alert=True)
            return
        
        # Проверяем права
        member = await project_repo.get_member(project_id, callback.from_user.id)
        if not member or member.role not in [RoleType.PROJECTNIK, RoleType.MAIN_ORGANIZER]:
            await callback.answer("❌ Нет доступа к настройкам", show_alert=True)
            return
    
    status = "✅ включены" if project.reminders_enabled else "❌ выключены"
    
    text = (
        f"🔔 <b>Настройки напоминаний</b>\n"
        f"📁 Проект: {project.name}\n\n"
        f"📊 <b>Текущие настройки:</b>\n"
        f"• Статус: {status}\n"
        f"• Время: <b>{project.reminder_hour:02d}:{project.reminder_minute:02d}</b> (МСК)\n"
        f"• Напоминать за: <b>{project.reminder_days_before}</b> дн. до дедлайна\n\n"
        f"<i>Напоминания отправляются всем ответственным за задачи с приближающимися дедлайнами</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_reminders_settings_keyboard(
            project_id=project_id,
            enabled=project.reminders_enabled,
            hour=project.reminder_hour,
            minute=project.reminder_minute,
            days_before=project.reminder_days_before,
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reminder:") & F.data.endswith(":toggle"))
async def callback_toggle_reminders(callback: CallbackQuery):
    """Включить/выключить напоминания"""
    project_id = int(callback.data.split(":")[1])
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        
        if not project:
            await callback.answer("❌ Проект не найден", show_alert=True)
            return
        
        # Переключаем
        project.reminders_enabled = not project.reminders_enabled
        new_status = project.reminders_enabled
    
    status_text = "🔔 Напоминания включены!" if new_status else "🔕 Напоминания выключены"
    await callback.answer(status_text, show_alert=False)
    
    # Обновляем сообщение
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
    
    status = "✅ включены" if project.reminders_enabled else "❌ выключены"
    
    text = (
        f"🔔 <b>Настройки напоминаний</b>\n"
        f"📁 Проект: {project.name}\n\n"
        f"📊 <b>Текущие настройки:</b>\n"
        f"• Статус: {status}\n"
        f"• Время: <b>{project.reminder_hour:02d}:{project.reminder_minute:02d}</b> (МСК)\n"
        f"• Напоминать за: <b>{project.reminder_days_before}</b> дн. до дедлайна\n\n"
        f"<i>Напоминания отправляются всем ответственным за задачи с приближающимися дедлайнами</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_reminders_settings_keyboard(
            project_id=project_id,
            enabled=project.reminders_enabled,
            hour=project.reminder_hour,
            minute=project.reminder_minute,
            days_before=project.reminder_days_before,
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("reminder:") & F.data.endswith(":time"))
async def callback_select_reminder_time(callback: CallbackQuery):
    """Выбор времени напоминаний"""
    project_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "⏰ <b>Выберите время напоминаний</b>\n\n"
        "<i>Время указано по Москве (МСК)</i>",
        reply_markup=get_reminder_time_keyboard(project_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reminder:") & F.data.contains(":set_time:"))
async def callback_set_reminder_time(callback: CallbackQuery):
    """Установка времени напоминаний"""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    hour = int(parts[3])
    minute = int(parts[4])
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        
        if not project:
            await callback.answer("❌ Проект не найден", show_alert=True)
            return
        
        project.reminder_hour = hour
        project.reminder_minute = minute
    
    logger.info(f"Project {project_id} reminder time set to {hour:02d}:{minute:02d}")
    await callback.answer(f"✅ Время установлено: {hour:02d}:{minute:02d}", show_alert=False)
    
    # Возвращаемся к настройкам
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
    
    status = "✅ включены" if project.reminders_enabled else "❌ выключены"
    
    text = (
        f"🔔 <b>Настройки напоминаний</b>\n"
        f"📁 Проект: {project.name}\n\n"
        f"📊 <b>Текущие настройки:</b>\n"
        f"• Статус: {status}\n"
        f"• Время: <b>{project.reminder_hour:02d}:{project.reminder_minute:02d}</b> (МСК)\n"
        f"• Напоминать за: <b>{project.reminder_days_before}</b> дн. до дедлайна\n\n"
        f"<i>Напоминания отправляются всем ответственным за задачи с приближающимися дедлайнами</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_reminders_settings_keyboard(
            project_id=project_id,
            enabled=project.reminders_enabled,
            hour=project.reminder_hour,
            minute=project.reminder_minute,
            days_before=project.reminder_days_before,
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("reminder:") & F.data.endswith(":custom_time"))
async def callback_custom_reminder_time(callback: CallbackQuery, state: FSMContext):
    """Ввод времени вручную"""
    project_id = int(callback.data.split(":")[1])
    
    await state.update_data(reminder_project_id=project_id)
    await state.set_state(ReminderStates.waiting_for_custom_time)
    
    await callback.message.edit_text(
        "⏰ <b>Введите время напоминаний</b>\n\n"
        "Формат: <code>ЧЧ:ММ</code>\n"
        "<i>Например: 09:30 или 14:00</i>\n\n"
        "⚠️ Время по Москве (МСК)",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ReminderStates.waiting_for_custom_time)
async def process_custom_reminder_time(message: Message, state: FSMContext):
    """Обработка введённого времени"""
    data = await state.get_data()
    project_id = data["reminder_project_id"]
    
    text = message.text.strip()
    
    try:
        parts = text.split(":")
        if len(parts) != 2:
            raise ValueError()
        
        hour = int(parts[0])
        minute = int(parts[1])
        
        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            raise ValueError()
            
    except (ValueError, IndexError):
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Используйте: <code>ЧЧ:ММ</code>\n"
            "<i>Например: 09:30 или 14:00</i>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        
        if not project:
            await message.answer("❌ Проект не найден")
            await state.clear()
            return
        
        project.reminder_hour = hour
        project.reminder_minute = minute
    
    await state.clear()
    logger.info(f"Project {project_id} reminder time set to {hour:02d}:{minute:02d}")
    
    # Показываем настройки
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
    
    status = "✅ включены" if project.reminders_enabled else "❌ выключены"
    
    text = (
        f"✅ <b>Время установлено: {hour:02d}:{minute:02d}</b>\n\n"
        f"🔔 <b>Настройки напоминаний</b>\n"
        f"📁 Проект: {project.name}\n\n"
        f"📊 <b>Текущие настройки:</b>\n"
        f"• Статус: {status}\n"
        f"• Время: <b>{project.reminder_hour:02d}:{project.reminder_minute:02d}</b> (МСК)\n"
        f"• Напоминать за: <b>{project.reminder_days_before}</b> дн. до дедлайна"
    )
    
    await message.answer(
        text,
        reply_markup=get_reminders_settings_keyboard(
            project_id=project_id,
            enabled=project.reminders_enabled,
            hour=project.reminder_hour,
            minute=project.reminder_minute,
            days_before=project.reminder_days_before,
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("reminder:") & F.data.endswith(":days"))
async def callback_select_reminder_days(callback: CallbackQuery):
    """Выбор за сколько дней напоминать"""
    project_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "📅 <b>За сколько дней напоминать?</b>\n\n"
        "<i>Напоминания будут отправляться участникам с задачами,\n"
        "до дедлайна которых осталось указанное количество дней или меньше</i>",
        reply_markup=get_reminder_days_keyboard(project_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reminder:") & F.data.contains(":set_days:"))
async def callback_set_reminder_days(callback: CallbackQuery):
    """Установка дней напоминания"""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    days = int(parts[3])
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        
        if not project:
            await callback.answer("❌ Проект не найден", show_alert=True)
            return
        
        project.reminder_days_before = days
    
    logger.info(f"Project {project_id} reminder days set to {days}")
    
    days_word = "день" if days == 1 else ("дня" if days in [2, 3, 4] else "дней")
    await callback.answer(f"✅ Установлено: за {days} {days_word}", show_alert=False)
    
    # Возвращаемся к настройкам
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
    
    status = "✅ включены" if project.reminders_enabled else "❌ выключены"
    
    text = (
        f"🔔 <b>Настройки напоминаний</b>\n"
        f"📁 Проект: {project.name}\n\n"
        f"📊 <b>Текущие настройки:</b>\n"
        f"• Статус: {status}\n"
        f"• Время: <b>{project.reminder_hour:02d}:{project.reminder_minute:02d}</b> (МСК)\n"
        f"• Напоминать за: <b>{project.reminder_days_before}</b> дн. до дедлайна\n\n"
        f"<i>Напоминания отправляются всем ответственным за задачи с приближающимися дедлайнами</i>"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_reminders_settings_keyboard(
            project_id=project_id,
            enabled=project.reminders_enabled,
            hour=project.reminder_hour,
            minute=project.reminder_minute,
            days_before=project.reminder_days_before,
        ),
        parse_mode="HTML",
    )

