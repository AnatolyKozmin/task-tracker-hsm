from typing import Optional, List

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project, ProjectMember, User, RoleType, ROLE_LIMITS


class ProjectRepository:
    """Репозиторий для работы с проектами"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        name: str,
        created_by: int,
        description: Optional[str] = None,
    ) -> Project:
        """Создать проект"""
        project = Project(
            name=name,
            description=description,
            created_by=created_by,
        )
        self.session.add(project)
        await self.session.flush()
        
        # Автоматически добавляем создателя как проектника
        member = ProjectMember(
            project_id=project.id,
            user_id=created_by,
            role=RoleType.PROJECTNIK.value,
        )
        self.session.add(member)
        await self.session.flush()
        
        return project
    
    async def get_by_id(self, project_id: int) -> Optional[Project]:
        """Получить проект по ID"""
        result = await self.session.execute(
            select(Project)
            .options(selectinload(Project.members).selectinload(ProjectMember.user))
            .options(selectinload(Project.tasks))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_projects(self) -> List[Project]:
        """Получить все активные проекты"""
        result = await self.session.execute(
            select(Project)
            .options(selectinload(Project.members))
            .where(Project.is_active == True)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_user_projects(self, telegram_id: int) -> List[Project]:
        """Получить проекты пользователя"""
        result = await self.session.execute(
            select(Project)
            .join(ProjectMember)
            .where(
                and_(
                    ProjectMember.user_id == telegram_id,
                    Project.is_active == True,
                )
            )
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def add_member(
        self,
        project_id: int,
        user_id: int,
        role: RoleType = RoleType.MEMBER,
    ) -> tuple[Optional[ProjectMember], str]:
        """
        Добавить участника в проект.
        Возвращает (member, error_message)
        """
        # Проверяем, не является ли пользователь уже участником
        existing = await self.session.execute(
            select(ProjectMember).where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            return None, "Пользователь уже является участником проекта"
        
        # Проверяем лимит ролей
        limit = ROLE_LIMITS.get(role)
        if limit is not None:
            count_result = await self.session.execute(
                select(ProjectMember).where(
                    and_(
                        ProjectMember.project_id == project_id,
                        ProjectMember.role == role.value,
                    )
                )
            )
            current_count = len(count_result.scalars().all())
            if current_count >= limit:
                return None, f"Достигнут лимит для роли ({limit})"
        
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role.value,
        )
        self.session.add(member)
        await self.session.flush()
        return member, ""
    
    async def remove_member(self, project_id: int, user_id: int) -> bool:
        """Удалить участника из проекта"""
        result = await self.session.execute(
            select(ProjectMember).where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                )
            )
        )
        member = result.scalar_one_or_none()
        if member:
            await self.session.delete(member)
            return True
        return False
    
    async def change_member_role(
        self,
        project_id: int,
        user_id: int,
        new_role: RoleType,
    ) -> tuple[Optional[ProjectMember], str]:
        """Изменить роль участника"""
        result = await self.session.execute(
            select(ProjectMember).where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                )
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return None, "Участник не найден"
        
        # Проверяем лимит новой роли
        limit = ROLE_LIMITS.get(new_role)
        if limit is not None:
            count_result = await self.session.execute(
                select(ProjectMember).where(
                    and_(
                        ProjectMember.project_id == project_id,
                        ProjectMember.role == new_role.value,
                    )
                )
            )
            current_count = len(count_result.scalars().all())
            if current_count >= limit:
                return None, f"Достигнут лимит для роли ({limit})"
        
        member.role = new_role.value
        return member, ""
    
    async def get_project_members(self, project_id: int) -> List[ProjectMember]:
        """Получить всех участников проекта"""
        result = await self.session.execute(
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(ProjectMember.project_id == project_id)
        )
        return list(result.scalars().all())
    
    async def get_member(self, project_id: int, user_id: int) -> Optional[ProjectMember]:
        """Получить участника проекта"""
        result = await self.session.execute(
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def deactivate(self, project_id: int) -> bool:
        """Деактивировать проект"""
        project = await self.get_by_id(project_id)
        if project:
            project.is_active = False
            return True
        return False
    
    async def update(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Project]:
        """Обновить проект"""
        project = await self.get_by_id(project_id)
        if project:
            if name:
                project.name = name
            if description is not None:
                project.description = description
        return project

