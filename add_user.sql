-- SQL скрипт для добавления пользователя в базу данных
-- Использование: docker-compose exec -T db psql -U vshu_bot vshu_bot_db < add_user.sql

-- Пример: Добавить пользователя вручную
-- Замените значения на реальные данные пользователя

INSERT INTO users (telegram_id, username, first_name, last_name, is_admin, created_at, updated_at)
VALUES (
    123456789,                    -- telegram_id пользователя (получить можно у @userinfobot)
    'username',                  -- username (без @) или NULL
    'Имя',                       -- first_name
    'Фамилия',                   -- last_name (или NULL)
    false,                       -- is_admin (true/false)
    NOW(),                       -- created_at
    NOW()                        -- updated_at
)
ON CONFLICT (telegram_id) DO UPDATE
SET 
    username = EXCLUDED.username,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    updated_at = NOW();

-- После добавления пользователя, его можно добавить в проект через бота
-- или вручную через таблицу project_members
