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
    
    # Собираем все данные внутри сессии
    project_name = None
    user_tasks: Dict[int, List[dict]] = {}
    user_overdue: Dict[int, List[dict]] = {}
    
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        
        if not project or not project.reminders_enabled:
            return
        
        project_name = project.name
        reminder_days = project.reminder_days_before
        
        task_repo = TaskRepository(session)
        
        # Получаем задачи с учётом настроек проекта
        now = moscow_now()
        deadline_threshold = now + timedelta(days=reminder_days)
        
        # Получаем все задачи проекта с приближающимися дедлайнами
        tasks = await task_repo.get_project_tasks(project_id)
        
        # Фильтруем по дедлайну и статусу и собираем данные
        for task in tasks:
            if task.status in [TaskStatus.COMPLETED.value, TaskStatus.NOT_COMPLETED.value]:
                continue
            
            if not task.deadline:
                continue
            
            # Сравниваем с учётом timezone
            task_deadline = task.deadline
            if task_deadline.tzinfo is None:
                task_deadline = task_deadline.replace(tzinfo=timezone.utc)
            
            now_utc = now.astimezone(timezone.utc) if now.tzinfo else now
            threshold_utc = deadline_threshold.astimezone(timezone.utc) if deadline_threshold.tzinfo else deadline_threshold
            
            # Собираем данные задачи в словарь (не ORM объект)
            task_data = {
                "title": task.title,
                "deadline": task.deadline,
            }
            
            is_overdue = task_deadline < now_utc
            is_upcoming = task_deadline <= threshold_utc
            
            # Группируем по пользователям
            for assignee in task.assignees:
                user_id = assignee.user_id
                
                if is_overdue:
                    if user_id not in user_overdue:
                        user_overdue[user_id] = []
                    user_overdue[user_id].append(task_data)
                elif is_upcoming:
                    if user_id not in user_tasks:
                        user_tasks[user_id] = []
                    user_tasks[user_id].append(task_data)
    
    # Теперь отправляем сообщения (вне сессии, но с простыми данными)
    all_users = set(user_tasks.keys()) | set(user_overdue.keys())
    sent_count = 0
    
    for user_id in all_users:
        tasks_list = user_tasks.get(user_id, [])
        overdue_list = user_overdue.get(user_id, [])
        
        if not tasks_list and not overdue_list:
            continue
        
        message = f"🔔 <b>Напоминание от проекта \"{project_name}\"</b>\n\n"
        
        if overdue_list:
            message += "🚨 <b>ПРОСРОЧЕННЫЕ ЗАДАЧИ:</b>\n"
            message += "━━━━━━━━━━━━━━━━━━━━\n"
            for i, task_data in enumerate(overdue_list, 1):
                deadline_str = format_datetime(task_data["deadline"], with_year=True)
                deadline = task_data["deadline"]
                if deadline:
                    now_naive = moscow_now().replace(tzinfo=None)
                    deadline_naive = deadline.replace(tzinfo=None) if deadline.tzinfo else deadline
                    days_overdue = (now_naive - deadline_naive).days
                    overdue_text = f"просрочено на {days_overdue} дн." if days_overdue > 0 else "просрочено сегодня"
                else:
                    overdue_text = "просрочено"
                
                message += f"<b>{i}. {task_data['title']}</b>\n"
                message += f"   ⚠️ {overdue_text} | DDL: {deadline_str}\n\n"
            message += "\n"
        
        if tasks_list:
            message += "📋 <b>ПРИБЛИЖАЮЩИЕСЯ ДЕДЛАЙНЫ:</b>\n"
            message += "━━━━━━━━━━━━━━━━━━━━\n"
            for i, task_data in enumerate(tasks_list, 1):
                deadline_str = format_datetime(task_data["deadline"], with_year=True)
                
                # Определяем срочность и время до дедлайна
                deadline = task_data["deadline"]
                urgency_emoji = "📋"
                time_left = ""
                
                if deadline:
                    now_naive = moscow_now().replace(tzinfo=None)
                    deadline_naive = deadline.replace(tzinfo=None) if deadline.tzinfo else deadline
                    days_left = (deadline_naive - now_naive).days
                    hours_left = (deadline_naive - now_naive).total_seconds() / 3600
                    
                    if days_left < 0:
                        urgency_emoji = "🔴"
                        time_left = f"просрочено на {abs(days_left)} дн."
                    elif hours_left <= 24:
                        urgency_emoji = "🔴"
                        if hours_left < 1:
                            time_left = "менее часа!"
                        elif hours_left < 12:
                            time_left = f"через {int(hours_left)} ч."
                        else:
                            time_left = "сегодня!"
                    elif days_left <= 1:
                        urgency_emoji = "🔴"
                        time_left = "завтра!"
                    elif days_left <= 2:
                        urgency_emoji = "🟡"
                        time_left = f"через {days_left} дн."
                    else:
                        urgency_emoji = "🟢"
                        time_left = f"через {days_left} дн."
                
                message += f"{urgency_emoji} <b>{i}. {task_data['title']}</b>\n"
                message += f"   📅 {deadline_str} ({time_left})\n\n"
        
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
        logger.info(f"Sent {sent_count} reminders for project {project_id} ({project_name})")


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
