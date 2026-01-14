# Telegram Bot
FROM python:3.12-slim

WORKDIR /app

# Копируем requirements и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Запуск бота
CMD ["python", "main.py"]
