import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.handlers import setup_routers
from bot.services import setup_scheduler, shutdown_scheduler
from database.connection import init_db, close_db


def setup_logging():
    """Настройка логирования"""
    # Создаем директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Уровень логирования
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Очищаем существующие handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)
    
    # File handler с ротацией (10MB max, 5 файлов)
    file_handler = RotatingFileHandler(
        log_dir / "bot.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)
    
    # Отдельный файл для ошибок
    error_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(error_handler)
    
    # Уменьшаем уровень логов для некоторых библиотек
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


async def run_migrations():
    """Запуск миграций Alembic"""
    import subprocess
    import os
    
    logger = logging.getLogger(__name__)
    logger.info("Running database migrations...")
    
    try:
        # Запускаем alembic upgrade head
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            env=os.environ,
        )
        
        if result.returncode == 0:
            logger.info("Migrations completed successfully")
            if result.stdout:
                logger.debug(f"Migration output: {result.stdout}")
        else:
            logger.error(f"Migration failed: {result.stderr}")
            raise Exception(f"Migration failed: {result.stderr}")
            
    except FileNotFoundError:
        logger.warning("Alembic not found, skipping migrations")
    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise


async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger = logging.getLogger(__name__)
    
    # Запускаем миграции
    await run_migrations()
    
    # Инициализируем БД
    await init_db()
    logger.info("Database initialized")
    
    # Запускаем планировщик
    await setup_scheduler(bot)
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"Bot started: @{bot_info.username}")


async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger = logging.getLogger(__name__)
    
    # Останавливаем планировщик
    await shutdown_scheduler()
    
    # Закрываем БД
    await close_db()
    
    logger.info("Bot stopped")


async def main():
    """Главная функция"""
    # Настраиваем логирование
    logger = setup_logging()
    logger.info("Starting VShu Task Bot...")
    
    # Создаем бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    # Создаем диспетчер
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем роутеры
    dp.include_router(setup_routers())
    
    # Регистрируем обработчики запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        # Удаляем webhook и запускаем polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

