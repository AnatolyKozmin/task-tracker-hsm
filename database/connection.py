import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер подключения к базе данных"""
    
    def __init__(self):
        self.engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Контекстный менеджер для сессии"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
    
    async def close(self):
        """Закрытие подключения"""
        await self.engine.dispose()
        logger.info("Database connection closed")


# Глобальный экземпляр
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Получить менеджер БД"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def init_db():
    """Инициализация БД"""
    global _db_manager
    _db_manager = DatabaseManager()
    logger.info("Database manager initialized")
    return _db_manager


async def close_db():
    """Закрытие подключения к БД"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None

