#!/usr/bin/env python3
"""
Скрипт для локального запуска веб-интерфейса конструктора ролей (FastAPI)

Использование:
    python web/run_local.py

Или с указанием порта:
    PORT=8080 python web/run_local.py
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Устанавливаем переменные окружения для локального подключения к БД
# Если БД в Docker, используем localhost:5433
if 'POSTGRES_HOST' not in os.environ:
    os.environ['POSTGRES_HOST'] = 'localhost'
if 'POSTGRES_PORT' not in os.environ:
    os.environ['POSTGRES_PORT'] = '5433'  # Внешний порт из docker-compose
if 'POSTGRES_USER' not in os.environ:
    os.environ['POSTGRES_USER'] = 'vshu_bot'
if 'POSTGRES_DB' not in os.environ:
    os.environ['POSTGRES_DB'] = 'vshu_bot_db'
# POSTGRES_PASSWORD должен быть в .env файле

import uvicorn

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    print(f"🚀 Запуск веб-интерфейса конструктора ролей (FastAPI)...")
    print(f"📡 Адрес: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"🗄️  БД: {os.environ.get('POSTGRES_HOST')}:{os.environ.get('POSTGRES_PORT')}")
    print(f"⚠️  Убедитесь, что БД запущена и доступна!")
    print()
    
    uvicorn.run(
        "web.app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
