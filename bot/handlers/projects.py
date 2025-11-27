import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.connection import get_db_manager
from database.repositories import UserRepository, ProjectRepository
from database.models import RoleType, ROLE_NAMES
from bot.keyboards import (
    get_projects_keyboard,
    get_project_menu_keyboard,
    get_cancel_keyboard,
    get_confirmation_keyboard,
)
from bot.states import ProjectStates

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "projects:list")
async def callback_projects_list(callback: CallbackQuery):
    """Список проектов пользователя"""
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        projects = await project_repo.get_user_projects(callback.from_user.id)
    
    if projects:
        text = "📁 <b>Ваши проекты:</b>\n\nВыберите проект для просмотра:"
    else:
        text = (
            "📁 <b>У вас пока нет проектов</b>\n\n"
            "Создайте новый проект или попросите добавить вас в существующий."
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_projects_keyboard(projects),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.text == "/myprojects")
async def cmd_my_projects(message: Message):
    """Команда /myprojects"""
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        projects = await project_repo.get_user_projects(message.from_user.id)
    
    if projects:
        text = "📁 <b>Ваши проекты:</b>\n\nВыберите проект для просмотра:"
    else:
        text = (
            "📁 <b>У вас пока нет проектов</b>\n\n"
            "Создайте новый проект или попросите добавить вас в существующий."
        )
    
    await message.answer(
        text,
        reply_markup=get_projects_keyboard(projects),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "projects:create")
async def callback_create_project(callback: CallbackQuery, state: FSMContext):
    """Начало создания проекта"""
    await state.set_state(ProjectStates.waiting_for_name)
    
    await callback.message.edit_text(
        "📝 <b>Создание нового проекта</b>\n\n"
        "Введите название проекта:\n"
        "<i>Например: \"Однажды на Масловке\"</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ProjectStates.waiting_for_name)
async def process_project_name(message: Message, state: FSMContext):
    """Обработка названия проекта"""
    name = message.text.strip()
    
    if len(name) < 3:
        await message.answer(
            "❌ Название слишком короткое. Минимум 3 символа.\n"
            "Введите название еще раз:",
            reply_markup=get_cancel_keyboard(),
        )
        return
    
    if len(name) > 255:
        await message.answer(
            "❌ Название слишком длинное. Максимум 255 символов.\n"
            "Введите название еще раз:",
            reply_markup=get_cancel_keyboard(),
        )
        return
    
    await state.update_data(project_name=name)
    await state.set_state(ProjectStates.waiting_for_description)
    
    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        "Теперь введите описание проекта (или отправьте '-' чтобы пропустить):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(ProjectStates.waiting_for_description)
async def process_project_description(message: Message, state: FSMContext):
    """Обработка описания проекта"""
    data = await state.get_data()
    name = data["project_name"]
    
    description = None
    if message.text.strip() != "-":
        description = message.text.strip()
    
    db = get_db_manager()
    async with db.session() as session:
        user_repo = UserRepository(session)
        await user_repo.get_or_create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        
        project_repo = ProjectRepository(session)
        project = await project_repo.create(
            name=name,
            description=description,
            created_by=message.from_user.id,
        )
        project_id = project.id
    
    await state.clear()
    logger.info(f"Project created: {name} (ID: {project_id}) by user {message.from_user.id}")
    
    text = (
        f"🎉 <b>Проект создан!</b>\n\n"
        f"📁 <b>{name}</b>\n"
    )
    if description:
        text += f"📝 {description}\n"
    text += f"\n👤 Вы назначены проектником ({ROLE_NAMES[RoleType.PROJECTNIK.value]})"
    
    await message.answer(
        text,
        reply_markup=get_project_menu_keyboard(project_id, is_admin=True),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":menu"))
async def callback_project_menu(callback: CallbackQuery):
    """Меню проекта"""
    project_id = int(callback.data.split(":")[1])
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        
        if not project:
            await callback.answer("❌ Проект не найден", show_alert=True)
            return
        
        # Проверяем права (проектник или главный организатор)
        member = await project_repo.get_member(project_id, callback.from_user.id)
        is_admin = member and member.role in [RoleType.PROJECTNIK.value, RoleType.MAIN_ORGANIZER.value]
    
    text = f"📁 <b>{project.name}</b>\n"
    if project.description:
        text += f"\n📝 {project.description}\n"
    
    text += f"\n👥 Участников: {len(project.members)}"
    text += f"\n📋 Задач: {len(project.tasks)}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_project_menu_keyboard(project_id, is_admin=is_admin),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":settings"))
async def callback_project_settings(callback: CallbackQuery):
    """Настройки проекта"""
    project_id = int(callback.data.split(":")[1])
    
    from bot.keyboards import get_project_settings_keyboard
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
    
    reminder_status = "🔔 вкл" if project.reminders_enabled else "🔕 выкл"
    
    await callback.message.edit_text(
        f"⚙️ <b>Настройки проекта</b>\n"
        f"📁 {project.name}\n\n"
        f"📊 <b>Напоминания:</b> {reminder_status}\n"
        f"⏰ Время: {project.reminder_hour:02d}:{project.reminder_minute:02d} МСК\n"
        f"📅 За {project.reminder_days_before} дн. до дедлайна\n\n"
        f"Выберите действие:",
        reply_markup=get_project_settings_keyboard(project_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":edit_name"))
async def callback_edit_project_name(callback: CallbackQuery, state: FSMContext):
    """Редактирование названия проекта"""
    project_id = int(callback.data.split(":")[1])
    await state.update_data(edit_project_id=project_id)
    await state.set_state(ProjectStates.waiting_for_edit_name)
    
    await callback.message.edit_text(
        "✏️ Введите новое название проекта:",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


@router.message(ProjectStates.waiting_for_edit_name)
async def process_edit_project_name(message: Message, state: FSMContext):
    """Обработка нового названия"""
    data = await state.get_data()
    project_id = data["edit_project_id"]
    name = message.text.strip()
    
    if len(name) < 3 or len(name) > 255:
        await message.answer(
            "❌ Название должно быть от 3 до 255 символов.",
            reply_markup=get_cancel_keyboard(),
        )
        return
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.update(project_id, name=name)
    
    await state.clear()
    
    await message.answer(
        f"✅ Название изменено на: <b>{name}</b>",
        reply_markup=get_project_menu_keyboard(project_id, is_admin=True),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":edit_desc"))
async def callback_edit_project_desc(callback: CallbackQuery, state: FSMContext):
    """Редактирование описания проекта"""
    project_id = int(callback.data.split(":")[1])
    await state.update_data(edit_project_id=project_id)
    await state.set_state(ProjectStates.waiting_for_edit_description)
    
    await callback.message.edit_text(
        "📝 Введите новое описание проекта (или '-' чтобы удалить):",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


@router.message(ProjectStates.waiting_for_edit_description)
async def process_edit_project_desc(message: Message, state: FSMContext):
    """Обработка нового описания"""
    data = await state.get_data()
    project_id = data["edit_project_id"]
    
    description = None if message.text.strip() == "-" else message.text.strip()
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        await project_repo.update(project_id, description=description)
    
    await state.clear()
    
    await message.answer(
        "✅ Описание обновлено!",
        reply_markup=get_project_menu_keyboard(project_id, is_admin=True),
    )


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":delete"))
async def callback_delete_project(callback: CallbackQuery):
    """Подтверждение удаления проекта"""
    project_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "⚠️ <b>Вы уверены, что хотите удалить проект?</b>\n\n"
        "Это действие нельзя отменить. Все задачи будут удалены.",
        reply_markup=get_confirmation_keyboard(
            confirm_callback=f"project:{project_id}:confirm_delete",
            cancel_callback=f"project:{project_id}:settings",
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":confirm_delete"))
async def callback_confirm_delete_project(callback: CallbackQuery):
    """Удаление проекта"""
    project_id = int(callback.data.split(":")[1])
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        await project_repo.deactivate(project_id)
    
    logger.info(f"Project {project_id} deactivated by user {callback.from_user.id}")
    
    await callback.message.edit_text(
        "✅ Проект удален.",
        reply_markup=get_projects_keyboard([]),
    )
    await callback.answer()

