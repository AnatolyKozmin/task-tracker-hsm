import logging
from typing import Dict, List
from datetime import timedelta, timezone

from aiogram import Bot

from database.connection import get_db_manager
from database.repositories import TaskRepository, ProjectRepository
from database.models import Task, TaskStatus
from bot.utils import moscow_now, format_datetime

logger = logging.getLogger(__name__)


async def send_project_reminders(bot: Bot, project_id: int):
    """
    Отправка напоминаний для конкретного проекта.
    Учитывает настройки напоминаний проекта.
    """
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        
        if not project or not project.reminders_enabled:
            return
        
        task_repo = TaskRepository(session)
        
        # Получаем задачи с учётом настроек проекта
        now = moscow_now()
        deadline_threshold = now + timedelta(days=project.reminder_days_before)
        
        # Получаем все задачи проекта с приближающимися дедлайнами
        tasks = await task_repo.get_project_tasks(project_id)
        
        # Фильтруем по дедлайну и статусу
        upcoming_tasks = []
        overdue_tasks = []
        
        for task in tasks:
            if task.status in [TaskStatus.COMPLETED, TaskStatus.NOT_COMPLETED]:
                continue
            
            if not task.deadline:
                continue
            
            # Сравниваем с учётом timezone
            task_deadline = task.deadline
            if task_deadline.tzinfo is None:
                task_deadline = task_deadline.replace(tzinfo=timezone.utc)
            
            now_utc = now.astimezone(timezone.utc) if now.tzinfo else now
            threshold_utc = deadline_threshold.astimezone(timezone.utc) if deadline_threshold.tzinfo else deadline_threshold
            
            if task_deadline < now_utc:
                overdue_tasks.append(task)
            elif task_deadline <= threshold_utc:
                upcoming_tasks.append(task)
    
    # Группируем задачи по пользователям
    user_tasks: Dict[int, List[Task]] = {}
    user_overdue: Dict[int, List[Task]] = {}
    
    for task in upcoming_tasks:
        for assignee in task.assignees:
            user_id = assignee.user_id
            if user_id not in user_tasks:
                user_tasks[user_id] = []
            user_tasks[user_id].append(task)
    
    for task in overdue_tasks:
        for assignee in task.assignees:
            user_id = assignee.user_id
            if user_id not in user_overdue:
                user_overdue[user_id] = []
            user_overdue[user_id].append(task)
    
    all_users = set(user_tasks.keys()) | set(user_overdue.keys())
    sent_count = 0
    
    for user_id in all_users:
        tasks_list = user_tasks.get(user_id, [])
        overdue_list = user_overdue.get(user_id, [])
        
        if not tasks_list and not overdue_list:
            continue
        
        message = f"👋 <b>Напоминание от проекта \"{project.name}\"</b>\n\n"
        
        if overdue_list:
            message += "🚨 <b>ПРОСРОЧЕННЫЕ:</b>\n"
            for task in overdue_list:
                deadline_str = format_datetime(task.deadline)
                message += f"• <b>{task.title}</b>\n"
                message += f"  ⚠️ DDL был: {deadline_str}\n\n"
        
        if tasks_list:
            message += "📋 <b>Приближающиеся дедлайны:</b>\n"
            for task in tasks_list:
                deadline_str = format_datetime(task.deadline)
                
                # Определяем срочность
                if task.deadline:
                    now_naive = moscow_now().replace(tzinfo=None)
                    deadline_naive = task.deadline.replace(tzinfo=None) if task.deadline.tzinfo else task.deadline
                    days_left = (deadline_naive - now_naive).days
                    
                    if days_left <= 1:
                        urgency = "🔴"
                    elif days_left <= 2:
                        urgency = "🟡"
                    else:
                        urgency = "🟢"
                else:
                    urgency = "📋"
                
                message += f"• {urgency} <b>{task.title}</b>\n"
                message += f"  📅 DDL: {deadline_str}\n\n"
        
        message += "💪 <i>Удачи в работе!</i>"
        
        try:
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="HTML",
            )
            sent_count += 1
        except Exception as e:
            logger.warning(f"Failed to send reminder to user {user_id}: {e}")
    
    if sent_count > 0:
        logger.info(f"Sent {sent_count} reminders for project {project_id} ({project.name})")


async def send_all_reminders(bot: Bot):
    """
    Отправка напоминаний для всех проектов.
    Вызывается планировщиком каждую минуту для проверки.
    """
    now = moscow_now()
    current_hour = now.hour
    current_minute = now.minute
    
    logger.debug(f"Checking reminders at {current_hour:02d}:{current_minute:02d} MSK")
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        projects = await project_repo.get_active_projects()
    
    for project in projects:
        if not project.reminders_enabled:
            continue
        
        # Проверяем, совпадает ли время
        if project.reminder_hour == current_hour and project.reminder_minute == current_minute:
            logger.info(f"Sending reminders for project {project.id} ({project.name})")
            await send_project_reminders(bot, project.id)


async def send_task_reminders(bot: Bot, days_before: int = 3):
    """
    Старый метод для обратной совместимости.
    Отправляет напоминания для всех проектов сразу.
    """
    await send_all_reminders(bot)


async def send_deadline_notification(bot: Bot, task: Task, user_id: int):
    """Отправка уведомления о конкретном дедлайне"""
    project_name = task.project.name if task.project else "Неизвестный проект"
    deadline_str = format_datetime(task.deadline, with_year=True) if task.deadline else "?"
    
    message = (
        f"⏰ <b>Напоминание о дедлайне!</b>\n\n"
        f"📋 <b>{task.title}</b>\n"
        f"📁 Проект: {project_name}\n"
        f"📅 Дедлайн: {deadline_str} (МСК)\n\n"
        f"<i>Не забудьте выполнить задачу вовремя!</i>"
    )
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML",
        )
        logger.debug(f"Deadline notification sent to user {user_id} for task {task.id}")
    except Exception as e:
        logger.warning(f"Failed to send deadline notification to user {user_id}: {e}")
