# Telegram Bot
# Используем стабильную версию Debian Bookworm вместо Trixie
FROM python:3.12-slim-bookworm

WORKDIR /app

# Устанавливаем переменные окружения (раньше для лучшего кеширования)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# asyncpg и psycopg2-binary имеют бинарные wheels, 
# системные зависимости не требуются

# Копируем requirements и устанавливаем зависимости Python
# Это делается отдельно для лучшего кеширования слоёв
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения (в конце, чтобы изменения в коде не пересобирали зависимости)
COPY . .

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Запуск бота
CMD ["python", "main.py"]
