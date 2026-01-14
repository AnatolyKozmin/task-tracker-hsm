# Telegram Bot
# Используем стабильную версию Debian Bookworm вместо Trixie
FROM python:3.12-slim-bookworm

WORKDIR /app

# Устанавливаем переменные окружения (раньше для лучшего кеширования)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Устанавливаем системные зависимости для PostgreSQL (нужны для asyncpg)
# Отключаем проблемные репозитории и используем только основной
RUN echo "deb http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

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
