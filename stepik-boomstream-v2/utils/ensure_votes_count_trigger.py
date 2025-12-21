
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

def ensure_votes_count_trigger():
    # Используем psycopg2 напрямую для DDL
    url = os.environ.get('DATABASE_URL')
    if not url:
        print('DATABASE_URL not set!')
        return
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='questions' AND column_name='votes_count'")
    if not cur.fetchone():
        print('votes_count column not found, applying migration...')
        # Сначала пробуем создать только votes_count
        try:
            alter_sql = "ALTER TABLE questions ADD COLUMN IF NOT EXISTS votes_count INTEGER DEFAULT 0 NOT NULL;"
            cur.execute(alter_sql)
            print('votes_count column created.')
        except Exception as e:
            print(f'Error creating votes_count column:\n{e}')
        # Теперь пробуем применить остальной SQL-скрипт
        sql_path = os.path.join(os.path.dirname(__file__), '../migrations/add_votes_count_trigger.sql')
        with open(sql_path, encoding='utf-8') as f:
            sql = f.read()
        import re
        func_blocks = list(re.finditer(r'(CREATE[\s\S]+?\$\$[\s\S]+?\$\$ LANGUAGE plpgsql;)', sql, re.IGNORECASE))
        statements = []
        last_end = 0
        for match in func_blocks:
            before = sql[last_end:match.start()]
            for stmt in before.split(';'):
                if stmt.strip():
                    statements.append(stmt.strip())
            statements.append(match.group(1).strip())
            last_end = match.end()
        after = sql[last_end:]
        for stmt in after.split(';'):
            if stmt.strip():
                statements.append(stmt.strip())
        for statement in statements:
            stmt = statement.strip()
            if not stmt or stmt.startswith('--'):
                continue
            try:
                cur.execute(stmt)
            except Exception as e:
                print(f'Error executing statement:\n{stmt}\n{e}')
        # Пересчитать votes_count для всех вопросов (всегда после миграции)
        try:
            cur.execute("""
                UPDATE questions SET votes_count = (
                    SELECT COUNT(*) FROM question_votes WHERE question_id = questions.id
                );
            """)
            print('votes_count values recalculated for all questions.')
        except Exception as e:
            print(f'Error updating votes_count values:\n{e}')
        conn.commit()
        print('votes_count column and trigger migration complete.')
    else:
        # votes_count уже есть, но всегда пересчитываем при старте
        try:
            cur.execute("""
                UPDATE questions SET votes_count = (
                    SELECT COUNT(*) FROM question_votes WHERE question_id = questions.id
                );
            """)
            print('votes_count values recalculated for all questions (already existed).')
        except Exception as e:
            print(f'Error updating votes_count values (already existed):\n{e}')
        conn.commit()
    cur.close()
    conn.close()
