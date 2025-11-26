from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Task, TaskAssignee, TaskStatus, User


class TaskRepository:
    """Репозиторий для работы с задачами"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        project_id: int,
        title: str,
        created_by: int,
        description: Optional[str] = None,
        deadline: Optional[datetime] = None,
        assignee_ids: Optional[List[int]] = None,
    ) -> Task:
        """Создать задачу"""
        task = Task(
            project_id=project_id,
            title=title,
            description=description,
            deadline=deadline,
            created_by=created_by,
        )
        self.session.add(task)
        await self.session.flush()
        
        # Добавляем ответственных
        if assignee_ids:
            for user_id in assignee_ids:
                assignee = TaskAssignee(
                    task_id=task.id,
                    user_id=user_id,
                )
                self.session.add(assignee)
        
        await self.session.flush()
        return task
    
    async def get_by_id(self, task_id: int) -> Optional[Task]:
        """Получить задачу по ID"""
        result = await self.session.execute(
            select(Task)
            .options(selectinload(Task.assignees).selectinload(TaskAssignee.user))
            .options(selectinload(Task.project))
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_project_tasks(
        self,
        project_id: int,
        status: Optional[TaskStatus] = None,
    ) -> List[Task]:
        """Получить задачи проекта"""
        query = (
            select(Task)
            .options(selectinload(Task.assignees).selectinload(TaskAssignee.user))
            .where(Task.project_id == project_id)
        )
        if status:
            query = query.where(Task.status == status)
        
        query = query.order_by(Task.deadline.asc().nullslast(), Task.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_user_tasks(
        self,
        telegram_id: int,
        status: Optional[TaskStatus] = None,
        project_id: Optional[int] = None,
    ) -> List[Task]:
        """Получить задачи пользователя"""
        query = (
            select(Task)
            .join(TaskAssignee)
            .options(selectinload(Task.assignees).selectinload(TaskAssignee.user))
            .options(selectinload(Task.project))
            .where(TaskAssignee.user_id == telegram_id)
        )
        
        if status:
            query = query.where(Task.status == status)
        if project_id:
            query = query.where(Task.project_id == project_id)
        
        query = query.order_by(Task.deadline.asc().nullslast(), Task.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_pending_tasks_with_deadline(
        self,
        days_before: int = 3,
    ) -> List[Task]:
        """
        Получить невыполненные задачи с дедлайном в ближайшие N дней
        для отправки напоминаний
        """
        now = datetime.utcnow()
        deadline_threshold = now + timedelta(days=days_before)
        
        result = await self.session.execute(
            select(Task)
            .options(selectinload(Task.assignees).selectinload(TaskAssignee.user))
            .options(selectinload(Task.project))
            .where(
                and_(
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                    Task.deadline.isnot(None),
                    Task.deadline <= deadline_threshold,
                    Task.deadline >= now,
                )
            )
            .order_by(Task.deadline.asc())
        )
        return list(result.scalars().all())
    
    async def get_overdue_tasks(self) -> List[Task]:
        """Получить просроченные задачи"""
        now = datetime.utcnow()
        
        result = await self.session.execute(
            select(Task)
            .options(selectinload(Task.assignees).selectinload(TaskAssignee.user))
            .options(selectinload(Task.project))
            .where(
                and_(
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                    Task.deadline.isnot(None),
                    Task.deadline < now,
                )
            )
            .order_by(Task.deadline.asc())
        )
        return list(result.scalars().all())
    
    async def update_status(
        self,
        task_id: int,
        status: TaskStatus,
    ) -> Optional[Task]:
        """Обновить статус задачи"""
        task = await self.get_by_id(task_id)
        if task:
            task.status = status
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
            else:
                task.completed_at = None
        return task
    
    async def add_assignee(self, task_id: int, user_id: int) -> Optional[TaskAssignee]:
        """Добавить ответственного"""
        # Проверяем, не назначен ли уже
        existing = await self.session.execute(
            select(TaskAssignee).where(
                and_(
                    TaskAssignee.task_id == task_id,
                    TaskAssignee.user_id == user_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            return None
        
        assignee = TaskAssignee(
            task_id=task_id,
            user_id=user_id,
        )
        self.session.add(assignee)
        await self.session.flush()
        return assignee
    
    async def remove_assignee(self, task_id: int, user_id: int) -> bool:
        """Удалить ответственного"""
        result = await self.session.execute(
            select(TaskAssignee).where(
                and_(
                    TaskAssignee.task_id == task_id,
                    TaskAssignee.user_id == user_id,
                )
            )
        )
        assignee = result.scalar_one_or_none()
        if assignee:
            await self.session.delete(assignee)
            return True
        return False
    
    async def update(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        deadline: Optional[datetime] = None,
    ) -> Optional[Task]:
        """Обновить задачу"""
        task = await self.get_by_id(task_id)
        if task:
            if title:
                task.title = title
            if description is not None:
                task.description = description
            if deadline is not None:
                task.deadline = deadline
        return task
    
    async def delete(self, task_id: int) -> bool:
        """Удалить задачу"""
        task = await self.get_by_id(task_id)
        if task:
            await self.session.delete(task)
            return True
        return False
    
    async def get_tasks_for_user_reminder(
        self,
        telegram_id: int,
        days_before: int = 3,
    ) -> List[Task]:
        """Получить задачи пользователя для напоминания"""
        now = datetime.utcnow()
        deadline_threshold = now + timedelta(days=days_before)
        
        result = await self.session.execute(
            select(Task)
            .join(TaskAssignee)
            .options(selectinload(Task.project))
            .where(
                and_(
                    TaskAssignee.user_id == telegram_id,
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                    Task.deadline.isnot(None),
                    or_(
                        Task.deadline <= deadline_threshold,
                        Task.deadline < now,  # просроченные тоже
                    ),
                )
            )
            .order_by(Task.deadline.asc())
        )
        return list(result.scalars().all())

