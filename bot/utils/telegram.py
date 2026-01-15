"""Утилиты для работы с Telegram API"""

from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
import logging

logger = logging.getLogger(__name__)


async def safe_edit_text(
    message: Message | CallbackQuery,
    text: str,
    reply_markup=None,
    parse_mode: str = "HTML",
    **kwargs
) -> bool:
    """
    Безопасное редактирование текста сообщения.
    Игнорирует ошибку "message is not modified".
    
    Returns:
        True если успешно, False если ошибка
    """
    try:
        if isinstance(message, CallbackQuery):
            await message.message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                **kwargs
            )
        else:
            await message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                **kwargs
            )
        return True
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            # Игнорируем эту ошибку - сообщение уже такое же
            logger.debug(f"Message not modified (ignored): {message.message_id if isinstance(message, CallbackQuery) else message.message_id}")
            return False
        # Другие ошибки пробрасываем дальше
        raise
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        raise
