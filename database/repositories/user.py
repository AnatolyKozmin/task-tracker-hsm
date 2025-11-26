from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str] = None,
    ) -> tuple[User, bool]:
        """Получить или создать пользователя. Возвращает (user, created)"""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Обновляем данные пользователя
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            return user, False
        
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self.session.add(user)
        await self.session.flush()
        return user, True
    
    async def get_all(self) -> List[User]:
        """Получить всех пользователей"""
        result = await self.session.execute(select(User))
        return list(result.scalars().all())
    
    async def set_admin(self, telegram_id: int, is_admin: bool = True) -> Optional[User]:
        """Установить статус администратора"""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.is_admin = is_admin
        return user
    
    async def search_by_username(self, username: str) -> List[User]:
        """Поиск пользователей по username"""
        result = await self.session.execute(
            select(User).where(User.username.ilike(f"%{username}%"))
        )
        return list(result.scalars().all())

