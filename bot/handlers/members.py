import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.connection import get_db_manager
from database.repositories import UserRepository, ProjectRepository
from database.models import RoleType, ROLE_NAMES
from bot.keyboards import (
    get_members_keyboard,
    get_roles_keyboard,
    get_cancel_keyboard,
    get_confirmation_keyboard,
    get_member_actions_keyboard,
)
from bot.states import MemberStates

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":members"))
async def callback_project_members(callback: CallbackQuery):
    """Список участников проекта"""
    project_id = int(callback.data.split(":")[1])
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        project = await project_repo.get_by_id(project_id)
        members = await project_repo.get_project_members(project_id)
        
        # Проверяем права
        current_member = await project_repo.get_member(project_id, callback.from_user.id)
        can_manage = current_member and current_member.role in [RoleType.PROJECTNIK.value, RoleType.MAIN_ORGANIZER.value]
    
    text = f"👥 <b>Участники проекта \"{project.name}\":</b>\n\n"
    
    if not members:
        text += "Пока нет участников"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_members_keyboard(members, project_id, can_manage=can_manage),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("project:") & F.data.endswith(":add_member"))
async def callback_add_member(callback: CallbackQuery, state: FSMContext):
    """Начало добавления участника"""
    project_id = int(callback.data.split(":")[1])
    
    await state.update_data(add_member_project_id=project_id)
    await state.set_state(MemberStates.waiting_for_username)
    
    await callback.message.edit_text(
        "👤 <b>Добавление участника</b>\n\n"
        "Введите username пользователя (без @):\n"
        "<i>Пользователь должен был ранее написать боту</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(MemberStates.waiting_for_username)
async def process_member_username(message: Message, state: FSMContext):
    """Обработка username участника"""
    username = message.text.strip().lstrip("@")
    
    db = get_db_manager()
    async with db.session() as session:
        user_repo = UserRepository(session)
        users = await user_repo.search_by_username(username)
        
        if not users:
            await message.answer(
                "❌ Пользователь не найден.\n\n"
                "Убедитесь, что пользователь уже написал боту /start\n"
                "Введите username еще раз:",
                reply_markup=get_cancel_keyboard(),
            )
            return
        
        # Если найдено несколько, берем точное совпадение или первого
        user = next((u for u in users if u.username and u.username.lower() == username.lower()), users[0])
    
    await state.update_data(add_member_user_id=user.telegram_id, add_member_username=user.username)
    await state.set_state(MemberStates.waiting_for_role)
    
    data = await state.get_data()
    project_id = data["add_member_project_id"]
    
    await message.answer(
        f"✅ Найден пользователь: <b>{user.full_name}</b> (@{user.username})\n\n"
        "Выберите роль для участника:",
        reply_markup=get_roles_keyboard(project_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("role:"), MemberStates.waiting_for_role)
async def callback_select_role(callback: CallbackQuery, state: FSMContext):
    """Выбор роли для нового участника"""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    role_value = parts[2]
    
    try:
        role = RoleType(role_value)
    except ValueError:
        await callback.answer("❌ Неверная роль", show_alert=True)
        return
    
    data = await state.get_data()
    user_id = data["add_member_user_id"]
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        member, error = await project_repo.add_member(project_id, user_id, role)
        
        if error:
            await callback.message.edit_text(
                f"❌ {error}",
                reply_markup=get_roles_keyboard(project_id),
            )
            await callback.answer()
            return
        
        project = await project_repo.get_by_id(project_id)
    
    await state.clear()
    logger.info(f"Member {user_id} added to project {project_id} with role {role.value}")
    
    role_name = ROLE_NAMES.get(role.value, "Участник")
    
    await callback.message.edit_text(
        f"✅ <b>Участник добавлен!</b>\n\n"
        f"👤 @{data['add_member_username']}\n"
        f"📌 Роль: {role_name}",
        reply_markup=get_members_keyboard(
            await get_project_members_list(project_id),
            project_id,
            can_manage=True,
        ),
        parse_mode="HTML",
    )
    await callback.answer()


async def get_project_members_list(project_id: int):
    """Вспомогательная функция для получения участников"""
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        return await project_repo.get_project_members(project_id)


@router.callback_query(F.data.startswith("member:") & F.data.endswith(":menu"))
async def callback_member_menu(callback: CallbackQuery):
    """Меню действий с участником"""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    user_id = int(parts[2])
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        member = await project_repo.get_member(project_id, user_id)
        
        if not member:
            await callback.answer("❌ Участник не найден", show_alert=True)
            return
    
    role_name = ROLE_NAMES.get(member.role, "Участник")
    user_name = member.user.full_name if member.user else "Unknown"
    username = f"@{member.user.username}" if member.user and member.user.username else ""
    
    await callback.message.edit_text(
        f"👤 <b>{user_name}</b> {username}\n"
        f"📌 Роль: {role_name}\n\n"
        "Выберите действие:",
        reply_markup=get_member_actions_keyboard(project_id, user_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("member:") & F.data.endswith(":change_role"))
async def callback_change_member_role(callback: CallbackQuery, state: FSMContext):
    """Изменение роли участника"""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    user_id = int(parts[2])
    
    await state.update_data(
        change_role_project_id=project_id,
        change_role_user_id=user_id,
    )
    await state.set_state(MemberStates.waiting_for_role)
    
    await callback.message.edit_text(
        "🔄 <b>Выберите новую роль:</b>",
        reply_markup=get_roles_keyboard(project_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("role:"))
async def callback_change_role_select(callback: CallbackQuery, state: FSMContext):
    """Выбор новой роли (для изменения)"""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    role_value = parts[2]
    
    data = await state.get_data()
    user_id = data.get("change_role_user_id")
    
    if not user_id:
        await callback.answer("❌ Ошибка. Попробуйте снова.", show_alert=True)
        return
    
    try:
        role = RoleType(role_value)
    except ValueError:
        await callback.answer("❌ Неверная роль", show_alert=True)
        return
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        member, error = await project_repo.change_member_role(project_id, user_id, role)
        
        if error:
            await callback.message.edit_text(
                f"❌ {error}",
                reply_markup=get_roles_keyboard(project_id),
            )
            await callback.answer()
            return
    
    await state.clear()
    logger.info(f"Member {user_id} role changed to {role.value} in project {project_id}")
    
    role_name = ROLE_NAMES.get(role.value, "Участник")
    
    await callback.message.edit_text(
        f"✅ Роль изменена на: {role_name}",
        reply_markup=get_members_keyboard(
            await get_project_members_list(project_id),
            project_id,
            can_manage=True,
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("member:") & F.data.endswith(":remove"))
async def callback_remove_member(callback: CallbackQuery):
    """Подтверждение удаления участника"""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    user_id = int(parts[2])
    
    await callback.message.edit_text(
        "⚠️ <b>Удалить участника из проекта?</b>",
        reply_markup=get_confirmation_keyboard(
            confirm_callback=f"member:{project_id}:{user_id}:confirm_remove",
            cancel_callback=f"member:{project_id}:{user_id}:menu",
        ),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("member:") & F.data.endswith(":confirm_remove"))
async def callback_confirm_remove_member(callback: CallbackQuery):
    """Удаление участника"""
    parts = callback.data.split(":")
    project_id = int(parts[1])
    user_id = int(parts[2])
    
    db = get_db_manager()
    async with db.session() as session:
        project_repo = ProjectRepository(session)
        await project_repo.remove_member(project_id, user_id)
    
    logger.info(f"Member {user_id} removed from project {project_id}")
    
    await callback.message.edit_text(
        "✅ Участник удален из проекта.",
        reply_markup=get_members_keyboard(
            await get_project_members_list(project_id),
            project_id,
            can_manage=True,
        ),
    )
    await callback.answer()

