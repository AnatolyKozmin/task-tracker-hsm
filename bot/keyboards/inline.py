from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Project, Task, RoleType, TaskStatus, ROLE_NAMES, ProjectMember
from bot.utils.timezone import format_datetime


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📁 Мои проекты", callback_data="projects:list"),
    )
    builder.row(
        InlineKeyboardButton(text="📋 Мои задачи", callback_data="tasks:my"),
    )
    builder.row(
        InlineKeyboardButton(text="➕ Создать проект", callback_data="projects:create"),
    )
    return builder.as_markup()


def get_projects_keyboard(
    projects: List[Project],
    show_create: bool = True,
) -> InlineKeyboardMarkup:
    """Список проектов"""
    builder = InlineKeyboardBuilder()
    
    for project in projects:
        builder.row(
            InlineKeyboardButton(
                text=f"📁 {project.name}",
                callback_data=f"project:{project.id}:menu",
            )
        )
    
    if show_create:
        builder.row(
            InlineKeyboardButton(text="➕ Создать проект", callback_data="projects:create"),
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def get_project_menu_keyboard(
    project_id: int,
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    """Меню проекта"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📋 Задачи",
            callback_data=f"project:{project_id}:tasks",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="👥 Участники",
            callback_data=f"project:{project_id}:members",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="➕ Создать задачу",
            callback_data=f"project:{project_id}:create_task",
        ),
    )
    
    if is_admin:
        builder.row(
            InlineKeyboardButton(
                text="👤 Добавить участника",
                callback_data=f"project:{project_id}:add_member",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="⚙️ Настройки",
                callback_data=f"project:{project_id}:settings",
            ),
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 К проектам", callback_data="projects:list"),
    )
    return builder.as_markup()


def get_roles_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Выбор роли"""
    builder = InlineKeyboardBuilder()
    
    for role in RoleType:
        builder.row(
            InlineKeyboardButton(
                text=ROLE_NAMES[role],
                callback_data=f"role:{project_id}:{role.value}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"project:{project_id}:members",
        ),
    )
    return builder.as_markup()


def get_tasks_keyboard(
    tasks: List[Task],
    project_id: Optional[int] = None,
    show_create: bool = True,
) -> InlineKeyboardMarkup:
    """Список задач"""
    builder = InlineKeyboardBuilder()
    
    status_emoji = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.IN_PROGRESS: "🔄",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.DELAYED: "⚠️",
        TaskStatus.NOT_COMPLETED: "❌",
    }
    
    for task in tasks:
        emoji = status_emoji.get(task.status, "📋")
        deadline_str = ""
        if task.deadline:
            deadline_str = f" | {format_datetime(task.deadline)}"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{emoji} {task.title[:30]}{'...' if len(task.title) > 30 else ''}{deadline_str}",
                callback_data=f"task:{task.id}:menu",
            )
        )
    
    if show_create and project_id:
        builder.row(
            InlineKeyboardButton(
                text="➕ Создать задачу",
                callback_data=f"project:{project_id}:create_task",
            ),
        )
    
    if project_id:
        builder.row(
            InlineKeyboardButton(
                text="🔙 К проекту",
                callback_data=f"project:{project_id}:menu",
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"),
        )
    
    return builder.as_markup()


def get_task_menu_keyboard(task: Task, can_edit: bool = False) -> InlineKeyboardMarkup:
    """Меню задачи"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить статус",
            callback_data=f"task:{task.id}:change_status",
        ),
    )
    
    if can_edit:
        builder.row(
            InlineKeyboardButton(
                text="📝 Редактировать",
                callback_data=f"task:{task.id}:edit",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="👥 Ответственные",
                callback_data=f"task:{task.id}:assignees",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"task:{task.id}:delete",
            ),
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 К задачам",
            callback_data=f"project:{task.project_id}:tasks",
        ),
    )
    return builder.as_markup()


def get_task_status_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Выбор статуса задачи"""
    builder = InlineKeyboardBuilder()
    
    status_options = [
        (TaskStatus.COMPLETED, "✅ Выполнено"),
        (TaskStatus.IN_PROGRESS, "🔄 В работе"),
        (TaskStatus.DELAYED, "⚠️ Задерживаю"),
        (TaskStatus.NOT_COMPLETED, "❌ Не выполнено"),
        (TaskStatus.PENDING, "⏳ Ожидает"),
    ]
    
    for status, text in status_options:
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"task:{task_id}:status:{status.value}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"task:{task_id}:menu",
        ),
    )
    return builder.as_markup()


def get_members_keyboard(
    members: List[ProjectMember],
    project_id: int,
    can_manage: bool = False,
) -> InlineKeyboardMarkup:
    """Список участников проекта"""
    builder = InlineKeyboardBuilder()
    
    for member in members:
        role_name = ROLE_NAMES.get(member.role, "👤 Участник")
        user_name = member.user.full_name if member.user else "Unknown"
        
        if can_manage:
            builder.row(
                InlineKeyboardButton(
                    text=f"{role_name}: {user_name}",
                    callback_data=f"member:{project_id}:{member.user_id}:menu",
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=f"{role_name}: {user_name}",
                    callback_data="noop",
                )
            )
    
    if can_manage:
        builder.row(
            InlineKeyboardButton(
                text="👤 Добавить участника",
                callback_data=f"project:{project_id}:add_member",
            ),
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 К проекту",
            callback_data=f"project:{project_id}:menu",
        ),
    )
    return builder.as_markup()


def get_project_settings_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Настройки проекта"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить название",
            callback_data=f"project:{project_id}:edit_name",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📝 Изменить описание",
            callback_data=f"project:{project_id}:edit_desc",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔔 Настройки напоминаний",
            callback_data=f"project:{project_id}:reminders",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить проект",
            callback_data=f"project:{project_id}:delete",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"project:{project_id}:menu",
        ),
    )
    return builder.as_markup()


def get_reminders_settings_keyboard(
    project_id: int,
    enabled: bool,
    hour: int,
    minute: int,
    days_before: int,
) -> InlineKeyboardMarkup:
    """Настройки напоминаний проекта"""
    builder = InlineKeyboardBuilder()
    
    # Статус напоминаний
    status_text = "🔔 Напоминания: ВКЛ" if enabled else "🔕 Напоминания: ВЫКЛ"
    builder.row(
        InlineKeyboardButton(
            text=status_text,
            callback_data=f"reminder:{project_id}:toggle",
        ),
    )
    
    if enabled:
        # Время отправки
        builder.row(
            InlineKeyboardButton(
                text=f"⏰ Время: {hour:02d}:{minute:02d} МСК",
                callback_data=f"reminder:{project_id}:time",
            ),
        )
        
        # За сколько дней
        days_text = f"📅 За {days_before} дн. до дедлайна"
        builder.row(
            InlineKeyboardButton(
                text=days_text,
                callback_data=f"reminder:{project_id}:days",
            ),
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 К настройкам",
            callback_data=f"project:{project_id}:settings",
        ),
    )
    return builder.as_markup()


def get_reminder_time_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Выбор времени напоминаний"""
    builder = InlineKeyboardBuilder()
    
    # Популярные времена
    times = [
        ("🌅 07:00", 7, 0),
        ("☀️ 08:00", 8, 0),
        ("🌤 09:00", 9, 0),
        ("🕐 10:00", 10, 0),
        ("🕛 12:00", 12, 0),
        ("🌆 18:00", 18, 0),
        ("🌙 20:00", 20, 0),
        ("🌚 21:00", 21, 0),
    ]
    
    # По 2 кнопки в ряд
    for i in range(0, len(times), 2):
        row_buttons = []
        for j in range(2):
            if i + j < len(times):
                text, hour, minute = times[i + j]
                row_buttons.append(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=f"reminder:{project_id}:set_time:{hour}:{minute}",
                    )
                )
        builder.row(*row_buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="⌨️ Ввести вручную",
            callback_data=f"reminder:{project_id}:custom_time",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"project:{project_id}:reminders",
        ),
    )
    return builder.as_markup()


def get_reminder_days_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Выбор за сколько дней напоминать"""
    builder = InlineKeyboardBuilder()
    
    days_options = [
        ("1️⃣ За 1 день", 1),
        ("2️⃣ За 2 дня", 2),
        ("3️⃣ За 3 дня", 3),
        ("5️⃣ За 5 дней", 5),
        ("7️⃣ За неделю", 7),
        ("🔟 За 10 дней", 10),
    ]
    
    # По 2 кнопки в ряд
    for i in range(0, len(days_options), 2):
        row_buttons = []
        for j in range(2):
            if i + j < len(days_options):
                text, days = days_options[i + j]
                row_buttons.append(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=f"reminder:{project_id}:set_days:{days}",
                    )
                )
        builder.row(*row_buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"project:{project_id}:reminders",
        ),
    )
    return builder.as_markup()


def get_member_actions_keyboard(
    project_id: int,
    user_id: int,
) -> InlineKeyboardMarkup:
    """Действия с участником"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Изменить роль",
            callback_data=f"member:{project_id}:{user_id}:change_role",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить из проекта",
            callback_data=f"member:{project_id}:{user_id}:remove",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 К участникам",
            callback_data=f"project:{project_id}:members",
        ),
    )
    return builder.as_markup()


def get_confirmation_keyboard(
    confirm_callback: str,
    cancel_callback: str,
) -> InlineKeyboardMarkup:
    """Подтверждение действия"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=confirm_callback),
        InlineKeyboardButton(text="❌ Нет", callback_data=cancel_callback),
    )
    return builder.as_markup()


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data),
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Кнопка отмены"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
    )
    return builder.as_markup()


def get_assignees_selection_keyboard(
    members: List[ProjectMember],
    selected_ids: List[int],
    project_id: int,
    task_id: Optional[int] = None,
) -> InlineKeyboardMarkup:
    """Выбор ответственных за задачу"""
    builder = InlineKeyboardBuilder()
    
    for member in members:
        is_selected = member.user_id in selected_ids
        checkbox = "☑️" if is_selected else "⬜"
        user_name = member.user.full_name if member.user else "Unknown"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{checkbox} {user_name}",
                callback_data=f"select_assignee:{member.user_id}",
            )
        )
    
    if task_id:
        builder.row(
            InlineKeyboardButton(
                text="💾 Сохранить",
                callback_data=f"task:{task_id}:save_assignees",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=f"task:{task_id}:menu",
            ),
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="✅ Готово",
                callback_data="confirm_assignees",
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel",
            ),
        )
    
    return builder.as_markup()


def get_my_tasks_keyboard(tasks: List[Task]) -> InlineKeyboardMarkup:
    """Мои задачи с возможностью быстрой смены статуса"""
    builder = InlineKeyboardBuilder()
    
    status_emoji = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.IN_PROGRESS: "🔄",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.DELAYED: "⚠️",
        TaskStatus.NOT_COMPLETED: "❌",
    }
    
    for i, task in enumerate(tasks, 1):
        emoji = status_emoji.get(task.status, "📋")
        deadline_str = ""
        if task.deadline:
            deadline_str = f" | DDL: {format_datetime(task.deadline)}"
        
        project_name = task.project.name if task.project else "?"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{i}. {emoji} {task.title[:25]}{'...' if len(task.title) > 25 else ''}{deadline_str}",
                callback_data=f"task:{task.id}:menu",
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"),
    )
    return builder.as_markup()

