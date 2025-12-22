-- Миграция: добавление votes_count в questions и триггер для автоматического пересчёта

-- 1. Добавить поле votes_count
ALTER TABLE questions ADD COLUMN IF NOT EXISTS votes_count INTEGER DEFAULT 0 NOT NULL;

-- 2. Функция для пересчёта голосов
CREATE OR REPLACE FUNCTION public.update_votes_count() RETURNS TRIGGER AS $$
DECLARE
    qid INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        qid := OLD.question_id;
    ELSE
        qid := NEW.question_id;
    END IF;

    UPDATE public.questions
    SET votes_count = (
        SELECT COUNT(*) FROM public.question_votes WHERE question_id = qid
    )
    WHERE id = qid;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 3. Триггер на вставку голоса
DROP TRIGGER IF EXISTS trg_update_votes_count_insert ON question_votes;
CREATE TRIGGER trg_update_votes_count_insert
AFTER INSERT ON question_votes
FOR EACH ROW EXECUTE FUNCTION update_votes_count();

-- 4. Триггер на удаление голоса
DROP TRIGGER IF EXISTS trg_update_votes_count_delete ON question_votes;
CREATE TRIGGER trg_update_votes_count_delete
AFTER DELETE ON question_votes
FOR EACH ROW EXECUTE FUNCTION update_votes_count();

-- 5. Инициализация: пересчитать для всех вопросов
UPDATE questions SET votes_count = (
    SELECT COUNT(*) FROM question_votes WHERE question_id = questions.id
);
