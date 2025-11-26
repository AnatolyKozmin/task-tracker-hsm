from aiogram import Router

from bot.handlers.start import router as start_router
from bot.handlers.projects import router as projects_router
from bot.handlers.tasks import router as tasks_router
from bot.handlers.members import router as members_router
from bot.handlers.reminders import router as reminders_router
from bot.handlers.common import router as common_router


def setup_routers() -> Router:
    """Настройка всех роутеров"""
    router = Router()
    
    router.include_router(start_router)
    router.include_router(projects_router)
    router.include_router(tasks_router)
    router.include_router(members_router)
    router.include_router(reminders_router)
    router.include_router(common_router)
    
    return router

