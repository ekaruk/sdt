-- Добавление поля messages_count в таблицу telegram_topics
ALTER TABLE telegram_topics 
ADD COLUMN IF NOT EXISTS messages_count INTEGER DEFAULT 1 NOT NULL;

-- Установить значение 1 для существующих записей
UPDATE telegram_topics 
SET messages_count = 1 
WHERE messages_count IS NULL;
