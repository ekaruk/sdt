-- Добавление поля short_title в таблицу stepik_modules
ALTER TABLE stepik_modules ADD COLUMN IF NOT EXISTS short_title VARCHAR;

-- Заполняем короткие названия для существующих модулей
UPDATE stepik_modules SET short_title = 'Раздел 1' WHERE id = 561993;
UPDATE stepik_modules SET short_title = 'Раздел 2' WHERE id = 579296;
UPDATE stepik_modules SET short_title = 'Раздел 3' WHERE id = 564649;
UPDATE stepik_modules SET short_title = 'Раздел 4' WHERE id = 579297;
UPDATE stepik_modules SET short_title = 'Раздел 5' WHERE id = 611382;
UPDATE stepik_modules SET short_title = 'Раздел 6' WHERE id = 611383;

-- Если есть другие модули, можно добавить:
-- UPDATE stepik_modules SET short_title = CONCAT('Р', position) WHERE short_title IS NULL;
