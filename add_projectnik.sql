-- SQL скрипт для добавления проектника в проект
-- Использование: docker-compose exec -T db psql -U vshu_bot -p 5433 vshu_bot_db < add_projectnik.sql

-- ШАГ 1: Убедитесь, что пользователь есть в базе (если нет - добавьте через add_user.sql или через бота /start)

-- ШАГ 2: Найдите ID проекта (можно посмотреть в таблице projects)
-- SELECT id, name FROM projects;

-- ШАГ 3: Добавьте пользователя как проектника в проект
-- Замените значения:
--   - project_id: ID проекта (из шага 2)
--   - user_telegram_id: Telegram ID пользователя (получить у @userinfobot)

INSERT INTO project_members (project_id, user_id, role, joined_at)
VALUES (
    1,                          -- project_id (замените на реальный ID проекта)
    922109605,                  -- user_id (telegram_id пользователя)
    'projectnik',               -- role (projectnik, main_organizer, senior_tp, senior_pr, senior_content, member)
    NOW()                       -- joined_at
)
ON CONFLICT (project_id, user_id) DO UPDATE
SET 
    role = EXCLUDED.role,
    joined_at = EXCLUDED.joined_at;

-- Проверка:
-- SELECT pm.*, u.first_name, u.username, p.name as project_name
-- FROM project_members pm
-- JOIN users u ON pm.user_id = u.telegram_id
-- JOIN projects p ON pm.project_id = p.id
-- WHERE pm.role = 'projectnik';
