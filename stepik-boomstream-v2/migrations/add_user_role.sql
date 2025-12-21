-- Добавление поля role в таблицу users
-- Миграция: добавление системы ролей

-- Добавить колонку role (по умолчанию 0 - пользователь)
ALTER TABLE users ADD COLUMN role INTEGER DEFAULT 0 NOT NULL;

-- Создать индекс для быстрой фильтрации по ролям
CREATE INDEX idx_users_role ON users(role);

-- Опционально: назначить первого админа (замените email на нужный)
-- UPDATE users SET role = 2 WHERE email = 'admin@example.com';

-- Проверка: показать всех пользователей с их ролями
-- SELECT id, email, first_name, last_name, role FROM users ORDER BY id;
