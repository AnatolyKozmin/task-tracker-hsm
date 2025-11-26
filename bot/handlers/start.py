import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.connection import get_db_manager
from database.repositories import UserRepository
from bot.keyboards import get_main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()
    
    db = get_db_manager()
    async with db.session() as session:
        user_repo = UserRepository(session)
        user, created = await user_repo.get_or_create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        
        if created:
            logger.info(f"New user registered: {user.telegram_id} ({user.full_name})")
    
    welcome_text = (
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "🎯 Я бот для управления проектной деятельностью ССт ВШУ.\n\n"
        "📌 <b>Что я умею:</b>\n"
        "• Создавать проекты и управлять ими\n"
        "• Распределять роли участников\n"
        "• Ставить задачи с дедлайнами\n"
        "• Отслеживать статус выполнения\n"
        "• Напоминать о приближающихся дедлайнах\n\n"
        "👇 Выберите действие:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """Команда /menu - показать главное меню"""
    await state.clear()
    
    await message.answer(
        "📋 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = (
        "📖 <b>Справка по боту</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/menu - Главное меню\n"
        "/help - Эта справка\n"
        "/myprojects - Мои проекты\n"
        "/mytasks - Мои задачи\n\n"
        "<b>Роли в проекте:</b>\n"
        "🎯 Проектник - руководитель проекта (1)\n"
        "⭐ Главный организатор - (макс. 2)\n"
        "🔧 Старший ТП - (1)\n"
        "📢 Старший PR - (1)\n"
        "📝 Старший наполнения - (1)\n"
        "👤 Участник - без ограничений\n\n"
        "<b>Статусы задач:</b>\n"
        "⏳ Ожидает\n"
        "🔄 В работе\n"
        "✅ Выполнено\n"
        "⚠️ Задерживается\n"
        "❌ Не выполнено\n"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    await callback.message.edit_text(
        "📋 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Пустой callback"""
    await callback.answer()

