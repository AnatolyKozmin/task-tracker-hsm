import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.connection import get_db_manager
from database.repositories import ProjectRepository, TaskRepository
from database.models import TaskStatus, RoleType
from bot.keyboards import (
    get_tasks_keyboard,
    get_task_menu_keyboard,
    get_task_status_keyboard,
    get_cancel_keyboard,
    get_my_tasks_keyboard,
    get_assignees_selection_keyboard,
    get_main_menu_keyboard,
)
from bot.states import TaskStates
from bot.utils import moscow_now, format_datetime, parse_datetime
from bot.utils.telegram import safe_edit_text

router = Router()
logger = logging.getLogger(__name__)


STATUS_NAMES = {
    TaskStatus.PENDING.value: "⏳ Ожидает",
    TaskStatus.IN_PROGRESS.value: "🔄 В работе",
    TaskStatus.COMPLETED.value: "✅ Выполнено",
    TaskStatus.DELAYED.value: "⚠️ Задерживается",
    TaskStatus.NOT_COMPLETED.value: "❌ Не выполнено",
}


@router.callback_query(F.data == "tasks:my")
async def callback_my_tasks(callback: CallbackQuery):
    """Мои задачи"""
    from datetime import datetime
    
    db = get_db_manager()
    async with db.session() as session:
        task_repo = TaskRepository(session)
        tasks = await task_repo.get_user_tasks(
            callback.from_user.id,
            status=None,  # Все статусы кроме завершенных
        )
        # Фильтруем завершенные
        tasks = [t for t in tasks if t.status != TaskStatus.COMPLETED.value]
    
    if tasks:
        text = "📋 <b>Ваши активные задачи</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Сортируем задачи: сначала просроченные, потом по дедлайну
        now = moscow_now().replace(tzinfo=None)
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                0 if (t.deadline and t.deadline.replace(tzinfo=None) < now) else 1,
                t.deadline.replace(tzinfo=None) if t.deadline else datetime.max.replace(tzinfo=None)
            )
        )
        
        for i, task in enumerate(sorted_tasks, 1):
            status = STATUS_NAMES.get(task.status, "?")
            project_name = task.project.name if task.project else "?"
            
            # Определяем срочность
            urgency_emoji = ""
            deadline_text = ""
            
            if task.deadline:
                deadline_naive = task.deadline.replace(tzinfo=None) if task.deadline.tzinfo else task.deadline
                days_left = (deadline_naive - now).days
                hours_left = (deadline_naive - now).total_seconds() / 3600
                
                if days_left < 0:
                    urgency_emoji = "🔴"
                    deadline_text = f"⚠️ Просрочено на {abs(days_left)} дн."
                elif hours_left <= 24:
                    urgency_emoji = "🔴"
                    if hours_left < 1:
                        deadline_text = "⚠️ Менее часа!"
                    else:
                        deadline_text = f"⚠️ Через {int(hours_left)} ч."
                elif days_left <= 1:
                    urgency_emoji = "🔴"
                    deadline_text = "⚠️ Завтра!"
                elif days_left <= 2:
                    urgency_emoji = "🟡"
                    deadline_text = f"📅 Через {days_left} дн."
                else:
                    urgency_emoji = "🟢"
                    deadline_text = f"📅 Через {days_left} дн."
                
                deadline_text = f"\n   {deadline_text} | DDL: {format_datetime(task.deadline, with_year=True)}"
            
            text += f"{urgency_emoji} <b>{i}. {task.title}</b>\n"
            text += f"   {status} | 📁 {project_name}{deadline_text}\n\n"
    else:
        text = "📋 <b>У вас нет активных задач</b>\n\n🎉 Отличная работа!"
    
    await safe_edit_text(
        callback,
        text,
        reply_markup=get_my_tasks_keyboard(tasks) if tasks else get_main_menu_keyboard(),
    )
    await callback.answer()


@router.message(F.text == "/mytasks")
async def cmd_my_tasks(message: Message):
    """Команда /mytasks"""
    from datetime import datetime
    
    db = get_db_manager()
    async with db.session() as session:
        task_repo = TaskRepository(session)
        tasks = await task_repo.get_user_tasks(
            message.from_user.id,
            status=None,
        )
        tasks = [t for t in tasks if t.status != TaskStatus.COMPLETED.value]
    
    if tasks:
        text = "📋 <b>Ваши активные задачи</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Сортируем задачи: сначала просроченные, потом по дедлайну
        now = moscow_now().replace(tzinfo=None)
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                0 if (t.deadline and t.deadline.replace(tzinfo=None) < now) else 1,
                t.deadline.replace(tzinfo=None) if t.deadline else datetime.max.replace(tzinfo=None)
            )
        )
        
        for i, task in enumerate(sorted_tasks, 1):
            status = STATUS_NAMES.get(task.status, "?")
            project_name = task.project.name if task.project else "?"
            
            # Определяем срочность
            urgency_emoji = ""
            deadline_text = ""
            
            if task.deadline:
                deadline_naive = task.deadline.replace(tzinfo=None) if task.deadline.tzinfo else task.deadline
                days_left = (deadline_naive - now).days
                hours_left = (deadline_naive - now).total_seconds() / 3600
                
                if days_left < 0:
                    urgency_emoji = "🔴"
                    deadline_text = f"⚠️ Просрочено на {abs(days_left)} дн."
                elif hours_left <= 24:
                    urgency_emoji = "🔴"
                    if hours_left < 1:
                        deadline_text = "⚠️ Менее часа!"
                    else:
                        deadline_text = f"⚠️ Через {int(hours_left)} ч."
                elif days_left <= 1:
                    urgency_emoji = "🔴"
                    deadline_text = "⚠️ Завтра!"
                elif days_left <= 2:
                    urgency_emoji = "🟡"
                    deadline_text = f"📅 Через {days_left} дн."
                else:
                    urgency_emoji = "🟢"
                    deadline_text = f"📅 Через {days_left} дн."
                
                deadline_text = f"\n   {deadline_text} | DDL: {format_datetime(task.deadline, with_year=True)}"
            
            text += f"{urgency_emoji} <b>{i}. {task.title}</b>\n"
            text += f"   {status} | 📁 {project_name}{deadline_text}\n\n"
    else:
        text = "📋 <b>У вас нет активных задач</b>\n\n🎉 Отличная работа!"
    
    await message.answer(
        text,
        reply_markup=get_my_tasks_keyboard(tasks) if tasks else get_main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":tasks"))
async def callback_project_tasks(callback: CallbackQuery):
    """Задачи проекта"""
    project_id = int(callback.data.split(":")[1])
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        
        task_repo = TaskRepository(session)
        tasks = await task_repo.get_project_tasks(project_id)
    
    if tasks:
        text = f"📋 <b>Задачи проекта \"{project.name}\":</b>\n\n"
    else:
        text = f"📋 <b>В проекте \"{project.name}\" пока нет задач</b>\n\nСоздайте первую задачу!"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_tasks_keyboard(tasks, project_id=project_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":create_task"))
async def callback_create_task(callback: CallbackQuery, state: FSMContext):
    """Начало создания задачи"""
    project_id = int(callback.data.split(":")[1])
    
    await state.update_data(
        task_project_id=project_id,
        task_assignees=[],
    )
    await state.set_state(TaskStates.waiting_for_title)
    
    await callback.message.edit_text(
        "📝 <b>Создание новой задачи</b>\n\n"
        "Введите название задачи:\n"
        "<i>Например: \"Редактирование анкеты\"</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(TaskStates.waiting_for_title)
async def process_task_title(message: Message, state: FSMContext):
    """Обработка названия задачи"""
    title = message.text.strip()
    
    if len(title) < 3:
        await message.answer(
            "❌ Название слишком короткое. Минимум 3 символа.",
            reply_markup=get_cancel_keyboard(),
        )
        return
    
    await state.update_data(task_title=title)
    await state.set_state(TaskStates.waiting_for_description)
    
    await message.answer(
        f"✅ Название: <b>{title}</b>\n\n"
        "Введите описание задачи (или '-' чтобы пропустить):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(TaskStates.waiting_for_description)
async def process_task_description(message: Message, state: FSMContext):
    """Обработка описания задачи"""
    description = None if message.text.strip() == "-" else message.text.strip()
    
    await state.update_data(task_description=description)
    await state.set_state(TaskStates.waiting_for_deadline)
    
    await message.answer(
        "📅 Введите дедлайн в формате (время по МСК):\n"
        "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code> или <code>ДД.ММ ЧЧ:ММ</code>\n"
        "<i>Например: 13.01.2025 23:59 или 13.01 23:59</i>\n\n"
        "Или '-' чтобы пропустить:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(TaskStates.waiting_for_deadline)
async def process_task_deadline(message: Message, state: FSMContext):
    """Обработка дедлайна"""
    deadline = None
    
    if message.text.strip() != "-":
        try:
            deadline = parse_datetime(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ Неверный формат. Используйте:\n"
                "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code> или <code>ДД.ММ ЧЧ:ММ</code>",
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML",
            )
            return
    
    await state.update_data(task_deadline=deadline)
    await state.set_state(TaskStates.waiting_for_assignees)
    
    # Получаем участников проекта
    data = await state.get_data()
    project_id = data["task_project_id"]
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        members = await project_repo.get_project_members(project_id)
    
    await message.answer(
        "👥 <b>Выберите ответственных за задачу:</b>\n\n"
        "Нажмите на участников, чтобы назначить их ответственными.\n"
        "Когда закончите, нажмите \"✅ Готово\".",
        reply_markup=get_assignees_selection_keyboard(
            members=members,
            selected_ids=[],
            project_id=project_id,
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("select_assignee:"), TaskStates.waiting_for_assignees)
async def callback_select_assignee(callback: CallbackQuery, state: FSMContext):
    """Выбор ответственного"""
    user_id = int(callback.data.split(":")[1])
    
    data = await state.get_data()
    assignees = data.get("task_assignees", [])
    
    if user_id in assignees:
        assignees.remove(user_id)
    else:
        assignees.append(user_id)
    
    await state.update_data(task_assignees=assignees)
    
    project_id = data["task_project_id"]
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        members = await project_repo.get_project_members(project_id)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_assignees_selection_keyboard(
            members=members,
            selected_ids=assignees,
            project_id=project_id,
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_assignees", TaskStates.waiting_for_assignees)
async def callback_confirm_assignees(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора ответственных и создание задачи"""
    data = await state.get_data()
    
    project_id = data["task_project_id"]
    title = data["task_title"]
    description = data.get("task_description")
    deadline = data.get("task_deadline")
    assignees = data.get("task_assignees", [])
    
    db = get_db_manager()
    async with db.session() as session:
        task_repo = TaskRepository(session)
        task = await task_repo.create(
            project_id=project_id,
            title=title,
            description=description,
            deadline=deadline,
            created_by=callback.from_user.id,
            assignee_ids=assignees if assignees else None,
        )
        task_id = task.id
    
    await state.clear()
    logger.info(f"Task created: {title} (ID: {task_id}) in project {project_id}")
    
    text = f"✅ <b>Задача создана!</b>\n\n"
    text += f"📋 <b>{title}</b>\n"
    if description:
        text += f"📝 {description}\n"
    if deadline:
        text += f"📅 DDL: {format_datetime(deadline, with_year=True)} (МСК)\n"
    text += f"👥 Ответственных: {len(assignees)}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_task_menu_keyboard(
            type("Task", (), {"id": task_id, "project_id": project_id})(),
            can_edit=True,
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:") & F.data.endswith(":menu"))
async def callback_task_menu(callback: CallbackQuery):
    """Меню задачи"""
    task_id = int(callback.data.split(":")[1])
    
    db = get_db_manager()
    async with db.session() as session:
        task_repo = TaskRepository(session)
        task = await task_repo.get_by_id(task_id)
        
        if not task:
            await callback.answer("❌ Задача не найдена", show_alert=True)
            return
        
        project_repo = ProjectRepository(session)
        member = await project_repo.get_member(task.project_id, callback.from_user.id)
        can_edit = member and member.role in [RoleType.PROJECTNIK.value, RoleType.MAIN_ORGANIZER.value]
    
    status = STATUS_NAMES.get(task.status, "?")
    
    text = f"📋 <b>{task.title}</b>\n\n"
    text += f"📊 Статус: {status}\n"
    if task.description:
        text += f"📝 {task.description}\n"
    if task.deadline:
        text += f"📅 DDL: {format_datetime(task.deadline, with_year=True)} (МСК)\n"
    
    if task.assignees:
        text += "\n👥 <b>Ответственные:</b>\n"
        for assignee in task.assignees:
            user = assignee.user
            text += f"   • {user.full_name}\n"
    
    if task.project:
        text += f"\n📁 Проект: {task.project.name}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_task_menu_keyboard(task, can_edit=can_edit),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:") & F.data.endswith(":change_status"))
async def callback_change_task_status(callback: CallbackQuery):
    """Изменение статуса задачи"""
    task_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "📊 <b>Выберите новый статус задачи:</b>",
        reply_markup=get_task_status_keyboard(task_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:") & F.data.contains(":status:"))
async def callback_set_task_status(callback: CallbackQuery):
    """Установка статуса задачи"""
    parts = callback.data.split(":")
    task_id = int(parts[1])
    status_value = parts[3]
    
    try:
        new_status = TaskStatus(status_value)
    except ValueError:
        await callback.answer("❌ Неверный статус", show_alert=True)
        return
    
    db = get_db_manager()
    async with db.session() as session:
        task_repo = TaskRepository(session)
        task = await task_repo.update_status(task_id, new_status)
        
        if not task:
            await callback.answer("❌ Задача не найдена", show_alert=True)
            return
        
        project_repo = ProjectRepository(session)
        member = await project_repo.get_member(task.project_id, callback.from_user.id)
        can_edit = member and member.role in [RoleType.PROJECTNIK.value, RoleType.MAIN_ORGANIZER.value]
    
    logger.info(f"Task {task_id} status changed to {new_status.value} by user {callback.from_user.id}")
    
    status_name = STATUS_NAMES.get(new_status, "?")
    
    text = f"✅ Статус изменен на: {status_name}\n\n"
    text += f"📋 <b>{task.title}</b>\n"
    if task.deadline:
        text += f"📅 DDL: {format_datetime(task.deadline, with_year=True)} (МСК)"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_task_menu_keyboard(task, can_edit=can_edit),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:") & F.data.endswith(":delete"))
async def callback_delete_task(callback: CallbackQuery):
    """Подтверждение удаления задачи"""
    task_id = int(callback.data.split(":")[1])
    
    from bot.keyboards import get_confirmation_keyboard
    
    await callback.message.edit_text(
        "⚠️ <b>Вы уверены, что хотите удалить задачу?</b>\n\n"
        "Это действие нельзя отменить.",
        reply_markup=get_confirmation_keyboard(
            confirm_callback=f"task:{task_id}:confirm_delete",
            cancel_callback=f"task:{task_id}:menu",
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:") & F.data.endswith(":confirm_delete"))
async def callback_confirm_delete_task(callback: CallbackQuery):
    """Удаление задачи"""
    task_id = int(callback.data.split(":")[1])
    
    db = get_db_manager()
    async with db.session() as session:
        task_repo = TaskRepository(session)
        task = await task_repo.get_by_id(task_id)
        project_id = task.project_id if task else None
        await task_repo.delete(task_id)
    
    logger.info(f"Task {task_id} deleted by user {callback.from_user.id}")
    
    await callback.message.edit_text(
        "✅ Задача удалена.",
        reply_markup=get_tasks_keyboard([], project_id=project_id) if project_id else get_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:") & F.data.endswith(":edit"))
async def callback_edit_task(callback: CallbackQuery, state: FSMContext):
    """Редактирование задачи"""
    task_id = int(callback.data.split(":")[1])
    
    await state.update_data(edit_task_id=task_id)
    await state.set_state(TaskStates.waiting_for_edit_title)
    
    await callback.message.edit_text(
        "✏️ Введите новое название задачи (или '-' чтобы оставить текущее):",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


@router.message(TaskStates.waiting_for_edit_title)
async def process_edit_task_title(message: Message, state: FSMContext):
    """Обработка нового названия задачи"""
    data = await state.get_data()
    task_id = data["edit_task_id"]
    
    new_title = None if message.text.strip() == "-" else message.text.strip()
    
    if new_title and len(new_title) < 3:
        await message.answer(
            "❌ Название слишком короткое.",
            reply_markup=get_cancel_keyboard(),
        )
        return
    
    await state.update_data(edit_task_title=new_title)
    await state.set_state(TaskStates.waiting_for_edit_description)
    
    await message.answer(
        "📝 Введите новое описание (или '-' чтобы оставить/удалить):",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(TaskStates.waiting_for_edit_description)
async def process_edit_task_description(message: Message, state: FSMContext):
    """Обработка нового описания"""
    new_desc = None if message.text.strip() == "-" else message.text.strip()
    
    await state.update_data(edit_task_description=new_desc)
    await state.set_state(TaskStates.waiting_for_edit_deadline)
    
    await message.answer(
        "📅 Введите новый дедлайн (время по МСК):\n"
        "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code> или <code>ДД.ММ ЧЧ:ММ</code>\n"
        "Или '-' чтобы оставить:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )


@router.message(TaskStates.waiting_for_edit_deadline)
async def process_edit_task_deadline(message: Message, state: FSMContext):
    """Обработка нового дедлайна и сохранение"""
    data = await state.get_data()
    task_id = data["edit_task_id"]
    
    new_deadline = None
    skip_deadline = message.text.strip() == "-"
    
    if not skip_deadline:
        try:
            new_deadline = parse_datetime(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ Неверный формат. Используйте:\n"
                "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code> или <code>ДД.ММ ЧЧ:ММ</code>",
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML",
            )
            return
    
    db = get_db_manager()
    async with db.session() as session:
        task_repo = TaskRepository(session)
        
        title = data.get("edit_task_title")
        description = data.get("edit_task_description")
        
        # Если пользователь ввёл '-', не меняем дедлайн (передаём None)
        # Если ввёл дату, передаём new_deadline
        task = await task_repo.update(
            task_id=task_id,
            title=title,
            description=description,
            deadline=new_deadline if not skip_deadline else None,
        )
    
    await state.clear()
    
    await message.answer(
        "✅ Задача обновлена!",
        reply_markup=get_task_menu_keyboard(task, can_edit=True),
    )


@router.callback_query(F.data.startswith("task:") & F.data.endswith(":assignees"))
async def callback_task_assignees(callback: CallbackQuery, state: FSMContext):
    """Управление ответственными"""
    task_id = int(callback.data.split(":")[1])
    
    db = get_db_manager()
    async with db.session() as session:
        task_repo = TaskRepository(session)
        task = await task_repo.get_by_id(task_id)
        
        project_repo = ProjectRepository(session)
        members = await project_repo.get_project_members(task.project_id)
        
        current_assignees = [a.user_id for a in task.assignees]
    
    await state.update_data(
        edit_task_id=task_id,
        task_project_id=task.project_id,
        task_assignees=current_assignees,
    )
    
    await callback.message.edit_text(
        "👥 <b>Ответственные за задачу:</b>\n\n"
        "Выберите участников:",
        reply_markup=get_assignees_selection_keyboard(
            members=members,
            selected_ids=current_assignees,
            project_id=task.project_id,
            task_id=task_id,
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("select_assignee:"))
async def callback_toggle_assignee(callback: CallbackQuery, state: FSMContext):
    """Переключение ответственного (вне состояния создания)"""
    user_id = int(callback.data.split(":")[1])
    
    data = await state.get_data()
    assignees = data.get("task_assignees", [])
    task_id = data.get("edit_task_id")
    project_id = data.get("task_project_id")
    
    if user_id in assignees:
        assignees.remove(user_id)
    else:
        assignees.append(user_id)
    
    await state.update_data(task_assignees=assignees)
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        members = await project_repo.get_project_members(project_id)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_assignees_selection_keyboard(
            members=members,
            selected_ids=assignees,
            project_id=project_id,
            task_id=task_id,
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:") & F.data.endswith(":save_assignees"))
async def callback_save_assignees(callback: CallbackQuery, state: FSMContext):
    """Сохранение ответственных"""
    task_id = int(callback.data.split(":")[1])
    
    data = await state.get_data()
    new_assignees = set(data.get("task_assignees", []))
    
    db = get_db_manager()
    async with db.session() as session:
        task_repo = TaskRepository(session)
        task = await task_repo.get_by_id(task_id)
        
        current_assignees = set(a.user_id for a in task.assignees)
        
        # Удаляем тех, кого убрали
        for user_id in current_assignees - new_assignees:
            await task_repo.remove_assignee(task_id, user_id)
        
        # Добавляем новых
        for user_id in new_assignees - current_assignees:
            await task_repo.add_assignee(task_id, user_id)
        
        # Перезагружаем задачу
        task = await task_repo.get_by_id(task_id)
    
    await state.clear()
    
    await callback.message.edit_text(
        "✅ Ответственные обновлены!",
        reply_markup=get_task_menu_keyboard(task, can_edit=True),
    )
    await callback.answer()
