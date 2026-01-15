# 🌐 Настройка доступа к веб-интерфейсу из интернета

## Быстрый способ (для тестирования)

### 1. Обновите docker-compose.yml
Порт уже настроен для доступа из интернета (убрана привязка к 127.0.0.1).

### 2. Откройте порт в firewall

**Для Ubuntu/Debian (ufw):**
```bash
sudo ufw allow 5000/tcp
sudo ufw reload
```

**Для CentOS/RHEL (firewalld):**
```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

**Для iptables:**
```bash
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables-save
```

### 3. Перезапустите контейнеры
```bash
docker-compose down
docker-compose up -d
```

### 4. Проверьте доступ
Откройте в браузере: `http://ВАШ_IP_СЕРВЕРА:5000`

---

## Рекомендуемый способ (через Nginx с SSL)

Для продакшена рекомендуется использовать Nginx как reverse proxy с SSL-сертификатом.

### 1. Установите Nginx
```bash
sudo apt update
sudo apt install nginx
```

### 2. Создайте конфигурацию Nginx
```bash
sudo nano /etc/nginx/sites-available/task-tracker
```

Вставьте:
```nginx
server {
    listen 80;
    server_name ваш-домен.ru;  # или IP адрес

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Активируйте конфигурацию
```bash
sudo ln -s /etc/nginx/sites-available/task-tracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Настройте SSL (опционально, через Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ваш-домен.ru
```

### 5. Верните привязку к localhost в docker-compose.yml
Для безопасности верните привязку к 127.0.0.1:
```yaml
ports:
  - "127.0.0.1:${WEB_PORT:-5000}:5000"
```

---

## Проверка доступности

### Проверка порта
```bash
# С сервера
curl http://localhost:5000

# С другого компьютера
curl http://ВАШ_IP:5000
```

### Проверка firewall
```bash
# Ubuntu/Debian
sudo ufw status

# CentOS/RHEL
sudo firewall-cmd --list-ports
```

---

## Безопасность

⚠️ **Важно:**
- Для продакшена используйте HTTPS (SSL)
- Настройте firewall для ограничения доступа
- Рассмотрите использование VPN или авторизации
- Не оставляйте порт открытым без защиты

---

## Изменение порта

Если хотите использовать другой порт:

1. Измените `WEB_PORT` в `.env`:
```bash
WEB_PORT=8080
```

2. Обновите firewall:
```bash
sudo ufw allow 8080/tcp
```

3. Перезапустите:
```bash
docker-compose down
docker-compose up -d
```
