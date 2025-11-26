"""Утилиты для работы с московским временем"""

from datetime import datetime, timezone, timedelta

# Московский часовой пояс (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))


def moscow_now() -> datetime:
    """Получить текущее время по Москве"""
    return datetime.now(MOSCOW_TZ)


def to_moscow(dt: datetime) -> datetime:
    """Конвертировать datetime в московское время"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Если время без timezone, считаем что это UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(MOSCOW_TZ)


def to_utc(dt: datetime) -> datetime:
    """Конвертировать московское время в UTC для хранения в БД"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Если время без timezone, считаем что это московское
        dt = dt.replace(tzinfo=MOSCOW_TZ)
    
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def format_datetime(dt: datetime, with_year: bool = False) -> str:
    """Форматировать datetime в читаемый вид (московское время)"""
    if dt is None:
        return "не указан"
    
    moscow_dt = to_moscow(dt)
    
    if with_year:
        return moscow_dt.strftime("%d.%m.%Y %H:%M")
    return moscow_dt.strftime("%d.%m %H:%M")


def parse_datetime(text: str) -> datetime:
    """
    Парсит дату из текста в формате ДД.ММ.ГГГГ ЧЧ:ММ или ДД.ММ ЧЧ:ММ
    Возвращает UTC время для хранения в БД
    """
    text = text.strip()
    
    # Пробуем полный формат с годом
    try:
        dt = datetime.strptime(text, "%d.%m.%Y %H:%M")
        dt = dt.replace(tzinfo=MOSCOW_TZ)
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        pass
    
    # Пробуем короткий формат без года
    try:
        dt = datetime.strptime(text, "%d.%m %H:%M")
        now = moscow_now()
        dt = dt.replace(year=now.year, tzinfo=MOSCOW_TZ)
        
        # Если дата уже прошла в этом году, берем следующий год
        if dt < now:
            dt = dt.replace(year=now.year + 1)
        
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        pass
    
    raise ValueError(f"Неверный формат даты: {text}")

