# Веб-интерфейс конструктора ролей (FastAPI)

Веб-интерфейс для управления динамическими ролями в проектах.

## Быстрый запуск

### Вариант 1: Через скрипт (рекомендуется)

```bash
# Из корневой директории проекта
python web/run_local.py
```

### Вариант 2: Через uvicorn напрямую

```bash
# Из корневой директории проекта
uvicorn web.app:app --reload --host 127.0.0.1 --port 5000
```

### Вариант 3: С указанием порта

```bash
PORT=8080 python web/run_local.py
```

## Требования

1. **База данных должна быть запущена** (через Docker Compose):
   ```bash
   docker compose up -d db
   ```

2. **Переменные окружения** (из `.env` файла):
   - `POSTGRES_PASSWORD` - пароль БД
   - Остальные настройки БД (по умолчанию используются значения для локального подключения)

3. **Установленные зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

## Доступ

После запуска откройте в браузере:
- **Интерфейс**: http://localhost:5000
- **API документация (Swagger)**: http://localhost:5000/docs
- **Альтернативная документация (ReDoc)**: http://localhost:5000/redoc

## Настройка подключения к БД

По умолчанию скрипт `run_local.py` использует:
- Host: `localhost` (вместо `db` для Docker)
- Port: `5433` (внешний порт из docker-compose)

Если нужно изменить, установите переменные окружения:
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_USER=vshu_bot
export POSTGRES_DB=vshu_bot_db
export POSTGRES_PASSWORD=your_password
```

## Использование

1. Выберите проект из списка
2. Создайте роли с нужными разрешениями
3. Добавьте участников к ролям (Имя, Username, Telegram ID)
4. Настройте иерархию управления
