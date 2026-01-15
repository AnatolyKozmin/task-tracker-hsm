#!/usr/bin/env python3
"""
Скрипт для создания проекта в базе данных
Использование:
    python create_project.py
    python create_project.py --name "Название проекта" --description "Описание"
    docker-compose exec bot python create_project.py
"""

import asyncio
import sys
import argparse
from datetime import datetime

from database.connection import get_db_manager
from database.models import Project, User, ProjectRole
from bot.config import settings


async def create_project(project_name=None, project_description=None, auto_create_roles=False):
    """Создать проект с базовыми ролями"""
    
    # Подключение к БД
    db_manager = get_db_manager()
    
    try:
        async with db_manager.session() as session:
            # Проверяем, есть ли пользователи
            from sqlalchemy import select
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ В базе нет пользователей!")
                print("📝 Сначала добавьте пользователя через бота (/start) или через add_user.sql")
                return
            
            print(f"✅ Найден пользователь: {user.first_name} (ID: {user.telegram_id})")
            
            # Проверяем, есть ли уже проекты
            result = await session.execute(select(Project))
            existing_projects = result.scalars().all()
            
            if existing_projects:
                print(f"\n📋 Найдено проектов: {len(existing_projects)}")
                for p in existing_projects:
                    print(f"   - {p.name} (ID: {p.id}, активен: {p.is_active})")
                
                if not project_name:  # Только если не передан аргумент
                    response = input("\n❓ Создать новый проект? (y/n): ").strip().lower()
                    if response != 'y':
                        print("❌ Отменено")
                        return
            
            # Запрашиваем данные проекта
            if not project_name:
                print("\n📝 Введите данные проекта:")
                project_name = input("   Название проекта: ").strip()
                if not project_name:
                    print("❌ Название проекта не может быть пустым!")
                    return
                
                project_description = input("   Описание (необязательно): ").strip() or None
            
            # Создаем проект
            project = Project(
                name=project_name,
                description=project_description,
                is_active=True,
                created_by=user.telegram_id,
                reminders_enabled=True,
                reminder_hour=9,
                reminder_minute=0,
                reminder_days_before=3
            )
            
            session.add(project)
            await session.flush()  # Получаем ID проекта
            
            print(f"\n✅ Проект создан: {project.name} (ID: {project.id})")
            
            # Создаем базовые роли
            if not auto_create_roles:
                create_roles = input("\n❓ Создать базовые роли? (y/n): ").strip().lower()
            else:
                create_roles = 'y'
            
            if create_roles == 'y':
                roles_data = [
                    {
                        "name": "🎯 Проектник",
                        "description": "Руководитель проекта",
                        "level": 0,
                        "can_manage_roles": True,
                        "can_manage_tasks": True,
                        "can_manage_members": True,
                        "can_manage_settings": True,
                        "managed_by_role_ids": None
                    },
                    {
                        "name": "⭐ Главный организатор",
                        "description": "Главный организатор проекта",
                        "level": 1,
                        "can_manage_roles": False,
                        "can_manage_tasks": True,
                        "can_manage_members": True,
                        "can_manage_settings": False,
                        "managed_by_role_ids": None
                    },
                    {
                        "name": "👤 Участник",
                        "description": "Обычный участник проекта",
                        "level": 2,
                        "can_manage_roles": False,
                        "can_manage_tasks": True,
                        "can_manage_members": False,
                        "can_manage_settings": False,
                        "managed_by_role_ids": None
                    }
                ]
                
                created_roles = []
                for role_data in roles_data:
                    role = ProjectRole(
                        project_id=project.id,
                        **role_data
                    )
                    session.add(role)
                    created_roles.append(role)
                
                await session.flush()
                
                print(f"\n✅ Создано ролей: {len(created_roles)}")
                for role in created_roles:
                    print(f"   - {role.name} (ID: {role.id}, уровень: {role.level})")
            
            await session.commit()
            
            print(f"\n🎉 Готово! Проект '{project.name}' успешно создан!")
            print(f"📊 ID проекта: {project.id}")
            print(f"🌐 Откройте веб-интерфейс для управления ролями: http://localhost:5000")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await db_manager.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Создать проект в базе данных")
    parser.add_argument("--name", "-n", type=str, help="Название проекта")
    parser.add_argument("--description", "-d", type=str, help="Описание проекта")
    parser.add_argument("--auto-roles", action="store_true", help="Автоматически создать базовые роли")
    
    args = parser.parse_args()
    
    print("🚀 Создание проекта в базе данных\n")
    asyncio.run(create_project(
        project_name=args.name,
        project_description=args.description,
        auto_create_roles=args.auto_roles
    ))
