import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from bot.services.notifications import send_all_reminders

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


async def setup_scheduler(bot: Bot):
    """Настройка и запуск планировщика"""
    global scheduler
    
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    # Проверяем каждую минуту, нужно ли отправлять напоминания
    # (каждый проект имеет свои настройки времени)
    scheduler.add_job(
        send_all_reminders,
        CronTrigger(minute="*"),  # Каждую минуту
        args=[bot],
        id="check_reminders",
        name="Check and send project reminders",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Scheduler started. Checking reminders every minute.")


async def shutdown_scheduler():
    """Остановка планировщика"""
    global scheduler
    
    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("Scheduler stopped")
