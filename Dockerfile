# Telegram Bot
FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости для PostgreSQL (нужны для asyncpg)
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Запуск бота
CMD ["python", "main.py"]
