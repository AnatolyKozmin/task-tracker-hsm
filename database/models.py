from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    Integer,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TaskStatus(str, Enum):
    """Статусы задачи"""
    PENDING = "pending"           # Ожидает выполнения
    IN_PROGRESS = "in_progress"   # В работе
    COMPLETED = "completed"       # Выполнено
    DELAYED = "delayed"           # Задерживается
    NOT_COMPLETED = "not_completed"  # Не выполнено


class RoleType(str, Enum):
    """Типы ролей в проекте"""
    PROJECTNIK = "projectnik"           # Проектник (руководитель)
    MAIN_ORGANIZER = "main_organizer"   # Главный организатор
    SENIOR_TP = "senior_tp"             # Старший ТП
    SENIOR_PR = "senior_pr"             # Старший PR
    SENIOR_CONTENT = "senior_content"   # Старший наполнения
    MEMBER = "member"                   # Участник


# Лимиты на роли в проекте
ROLE_LIMITS = {
    RoleType.PROJECTNIK: 2,  # Изменено с 1 на 2
    RoleType.MAIN_ORGANIZER: 2,
    RoleType.SENIOR_TP: 1,
    RoleType.SENIOR_PR: 1,
    RoleType.SENIOR_CONTENT: 1,
    RoleType.MEMBER: None,  # Без ограничений
}

ROLE_NAMES = {
    RoleType.PROJECTNIK.value: "🎯 Проектник",
    RoleType.MAIN_ORGANIZER.value: "⭐ Главный организатор",
    RoleType.SENIOR_TP.value: "🔧 Старший ТП",
    RoleType.SENIOR_PR.value: "📢 Старший PR",
    RoleType.SENIOR_CONTENT.value: "📝 Старший наполнения",
    RoleType.MEMBER.value: "👤 Участник",
}


class User(Base):
    """Пользователь бота"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Отношения
    project_memberships: Mapped[List["ProjectMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    assigned_tasks: Mapped[List["TaskAssignee"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    
    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    @property
    def mention(self) -> str:
        if self.username:
            return f"@{self.username}"
        return f"[{self.full_name}](tg://user?id={self.telegram_id})"


class Project(Base):
    """Проект"""
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Настройки напоминаний
    reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_hour: Mapped[int] = mapped_column(Integer, default=9)  # Час по МСК
    reminder_minute: Mapped[int] = mapped_column(Integer, default=0)
    reminder_days_before: Mapped[int] = mapped_column(Integer, default=3)  # За сколько дней
    
    # Отношения
    members: Mapped[List["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    roles: Mapped[List["ProjectRole"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectRole(Base):
    """Динамическая роль в проекте с иерархией"""
    __tablename__ = "project_roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # Название роли
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=0)  # Уровень в иерархии (0 = самый высокий)
    can_manage_roles: Mapped[bool] = mapped_column(Boolean, default=False)  # Может управлять ролями
    can_manage_tasks: Mapped[bool] = mapped_column(Boolean, default=True)  # Может управлять задачами
    can_manage_members: Mapped[bool] = mapped_column(Boolean, default=False)  # Может управлять участниками
    can_manage_settings: Mapped[bool] = mapped_column(Boolean, default=False)  # Может управлять настройками
    managed_by_role_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON список ID ролей, которые управляют этой ролью
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Отношения
    project: Mapped["Project"] = relationship(back_populates="roles")
    members: Mapped[List["ProjectMember"]] = relationship(back_populates="role_obj")


class ProjectMember(Base):
    """Участник проекта с ролью"""
    __tablename__ = "project_members"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"))
    role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("project_roles.id", ondelete="SET NULL"), nullable=True)
    # Старое поле для обратной совместимости (будет удалено после миграции)
    role: Mapped[str] = mapped_column(String(50), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Уникальность: один пользователь - одна роль в проекте
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="unique_project_user"),
    )
    
    # Отношения
    project: Mapped["Project"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="project_memberships")
    role_obj: Mapped[Optional["ProjectRole"]] = relationship(back_populates="members")


class Task(Base):
    """Задача в проекте"""
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(String(50), default=TaskStatus.PENDING.value)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Отношения
    project: Mapped["Project"] = relationship(back_populates="tasks")
    assignees: Mapped[List["TaskAssignee"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class TaskAssignee(Base):
    """Ответственный за задачу"""
    __tablename__ = "task_assignees"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="unique_task_user"),
    )
    
    # Отношения
    task: Mapped["Task"] = relationship(back_populates="assignees")
    user: Mapped["User"] = relationship(back_populates="assigned_tasks")

