"""FastAPI приложение для управления ролями"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database.connection import get_db_manager
from database.repositories import ProjectRepository
from database.models import Project, ProjectRole, ProjectMember, User
from sqlalchemy import select
import json
from pathlib import Path

app = FastAPI(title="VShu Task Bot - Role Constructor")

# Настраиваем пути для шаблонов
web_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(web_dir / "templates"))


# Pydantic модели для API
class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    level: int = 0
    can_manage_roles: bool = False
    can_manage_tasks: bool = True
    can_manage_members: bool = False
    can_manage_settings: bool = False
    managed_by: List[int] = []


class RoleUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    level: int = 0
    can_manage_roles: bool = False
    can_manage_tasks: bool = True
    can_manage_members: bool = False
    can_manage_settings: bool = False
    managed_by: List[int] = []


class MemberAdd(BaseModel):
    role_id: int
    username: str  # Только username, без @


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница с конструктором ролей"""
    return templates.TemplateResponse("role_constructor.html", {"request": request})


@app.get("/api/projects")
async def get_projects():
    """Получить список проектов"""
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        projects = await project_repo.get_active_projects()
    
    return [{
        'id': p.id,
        'name': p.name,
        'description': p.description
    } for p in projects]


@app.get("/api/projects/{project_id}/roles")
async def get_project_roles(project_id: int):
    """Получить роли проекта"""
    db = get_db_manager()
    async with db.session() as session:
        result = await session.execute(
            select(ProjectRole).where(ProjectRole.project_id == project_id)
        )
        roles = result.scalars().all()
        
        # Получаем участников для каждой роли
        result = await session.execute(
            select(ProjectMember, User).join(User).where(
                ProjectMember.project_id == project_id
            )
        )
        members_data = result.all()
    
    roles_data = []
    for role in roles:
        # Находим участников с этой ролью
        members = [
            {
                'id': member.user_id,
                'name': user.full_name,
                'username': user.username
            }
            for member, user in members_data
            if member.role_id == role.id
        ]
        
        managed_by = []
        if role.managed_by_role_ids:
            try:
                managed_by = json.loads(role.managed_by_role_ids)
            except:
                pass
        
        roles_data.append({
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'level': role.level,
            'can_manage_roles': role.can_manage_roles,
            'can_manage_tasks': role.can_manage_tasks,
            'can_manage_members': role.can_manage_members,
            'can_manage_settings': role.can_manage_settings,
            'managed_by': managed_by,
            'members': members
        })
    
    return roles_data


@app.post("/api/projects/{project_id}/roles")
async def create_role(project_id: int, role_data: RoleCreate):
    """Создать новую роль"""
    db = get_db_manager()
    async with db.session() as session:
        role = ProjectRole(
            project_id=project_id,
            name=role_data.name,
            description=role_data.description,
            level=role_data.level,
            can_manage_roles=role_data.can_manage_roles,
            can_manage_tasks=role_data.can_manage_tasks,
            can_manage_members=role_data.can_manage_members,
            can_manage_settings=role_data.can_manage_settings,
            managed_by_role_ids=json.dumps(role_data.managed_by)
        )
        session.add(role)
        await session.flush()
        role_id = role.id
    
    return {'id': role_id, 'success': True}


@app.put("/api/projects/{project_id}/roles/{role_id}")
async def update_role(project_id: int, role_id: int, role_data: RoleUpdate):
    """Обновить роль"""
    db = get_db_manager()
    async with db.session() as session:
        result = await session.execute(
            select(ProjectRole).where(
                ProjectRole.id == role_id,
                ProjectRole.project_id == project_id
            )
        )
        role = result.scalar_one_or_none()
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        role.name = role_data.name
        role.description = role_data.description
        role.level = role_data.level
        role.can_manage_roles = role_data.can_manage_roles
        role.can_manage_tasks = role_data.can_manage_tasks
        role.can_manage_members = role_data.can_manage_members
        role.can_manage_settings = role_data.can_manage_settings
        role.managed_by_role_ids = json.dumps(role_data.managed_by)
    
    return {'success': True}


@app.delete("/api/projects/{project_id}/roles/{role_id}")
async def delete_role(project_id: int, role_id: int):
    """Удалить роль"""
    db = get_db_manager()
    async with db.session() as session:
        result = await session.execute(
            select(ProjectRole).where(
                ProjectRole.id == role_id,
                ProjectRole.project_id == project_id
            )
        )
        role = result.scalar_one_or_none()
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        await session.delete(role)
    
    return {'success': True}


@app.post("/api/projects/{project_id}/members")
async def add_member_to_role(project_id: int, member_data: MemberAdd):
    """Добавить участника к роли"""
    from database.repositories import UserRepository
    from bot.config import settings
    from aiogram import Bot
    
    db = get_db_manager()
    async with db.session() as session:
        # Ищем пользователя по username
        username = member_data.username.lstrip('@').lower()
        user_repo = UserRepository(session)
        users = await user_repo.search_by_username(username)
        
        # Ищем точное совпадение
        user = next(
            (u for u in users if u.username and u.username.lower() == username),
            None
        )
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"Пользователь @{username} не найден. Убедитесь, что пользователь написал боту /start"
            )
        
        # Проверяем роль
        result = await session.execute(
            select(ProjectRole).where(
                ProjectRole.id == member_data.role_id,
                ProjectRole.project_id == project_id
            )
        )
        role = result.scalar_one_or_none()
        
        if not role:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        
        # Проверяем, есть ли уже участник в проекте
        result = await session.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user.telegram_id
            )
        )
        member = result.scalar_one_or_none()
        
        if member:
            # Обновляем роль
            old_role_id = member.role_id
            member.role_id = member_data.role_id
        else:
            # Создаём нового участника
            member = ProjectMember(
                project_id=project_id,
                user_id=user.telegram_id,
                role_id=member_data.role_id
            )
            session.add(member)
        
        await session.flush()
        
        # Получаем информацию о проекте для уведомления
        result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        # Отправляем уведомление пользователю через бота
        if settings.bot_token:
            try:
                bot = Bot(token=settings.bot_token)
                
                # Формируем сообщение о роли
                role_message = f"🎯 <b>Вас назначили на роль в проекте!</b>\n\n"
                role_message += f"📁 <b>Проект:</b> {project.name if project else 'Неизвестный'}\n"
                role_message += f"👤 <b>Ваша роль:</b> {role.name}\n"
                
                if role.description:
                    role_message += f"📝 {role.description}\n"
                
                # Если это не проектник, показываем информацию о старшем
                if role.level > 0:
                    # Ищем роли, которые управляют этой ролью
                    if role.managed_by_role_ids:
                        try:
                            managed_by_ids = json.loads(role.managed_by_role_ids)
                            if managed_by_ids:
                                result = await session.execute(
                                    select(ProjectRole).where(
                                        ProjectRole.id.in_(managed_by_ids),
                                        ProjectRole.project_id == project_id
                                    )
                                )
                                manager_roles = result.scalars().all()
                                
                                if manager_roles:
                                    role_message += f"\n👔 <b>Ваш старший:</b> "
                                    role_message += ", ".join([r.name for r in manager_roles])
                        except:
                            pass
                
                role_message += "\n\n✅ Теперь вы можете работать с задачами проекта через бота!"
                
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=role_message,
                    parse_mode="HTML"
                )
                await bot.session.close()
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to send role notification to user {user.telegram_id}: {e}")
    
    return {'success': True}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
