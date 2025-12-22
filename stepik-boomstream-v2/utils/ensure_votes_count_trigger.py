import os
import re

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def ensure_votes_count_trigger():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL not set!")
        return

    conn = psycopg2.connect(url)
    cur = conn.cursor()

    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='questions' AND column_name='votes_count'"
    )
    if not cur.fetchone():
        print("votes_count column not found, applying migration...")
        try:
            alter_sql = (
                "ALTER TABLE questions "
                "ADD COLUMN IF NOT EXISTS votes_count INTEGER DEFAULT 0 NOT NULL;"
            )
            cur.execute(alter_sql)
            print("votes_count column created.")
        except Exception as e:
            print(f"Error creating votes_count column:\n{e}")
    else:
        print("votes_count column already exists.")

    sql_path = os.path.join(
        os.path.dirname(__file__), "../migrations/add_votes_count_trigger.sql"
    )
    with open(sql_path, encoding="utf-8") as f:
        sql = f.read()

    func_blocks = list(
        re.finditer(
            r"(CREATE[\s\S]+?\$\$[\s\S]+?\$\$ LANGUAGE plpgsql;)",
            sql,
            re.IGNORECASE,
        )
    )
    statements = []
    last_end = 0
    for match in func_blocks:
        before = sql[last_end:match.start()]
        for stmt in before.split(";"):
            if stmt.strip():
                statements.append(stmt.strip())
        statements.append(match.group(1).strip())
        last_end = match.end()
    after = sql[last_end:]
    for stmt in after.split(";"):
        if stmt.strip():
            statements.append(stmt.strip())

    cur.execute(
        "SELECT tgname FROM pg_trigger "
        "WHERE tgrelid = 'public.question_votes'::regclass "
        "AND NOT tgisinternal"
    )
    existing_triggers = {row[0] for row in cur.fetchall()}

    for statement in statements:
        stmt = statement.strip()
        if not stmt or stmt.startswith("--"):
            continue
        if stmt.upper().startswith("CREATE TRIGGER"):
            if "trg_update_votes_count_insert" in stmt and "trg_update_votes_count_insert" in existing_triggers:
                continue
            if "trg_update_votes_count_delete" in stmt and "trg_update_votes_count_delete" in existing_triggers:
                continue
        try:
            cur.execute(stmt)
        except Exception as e:
            print(f"Error executing statement:\n{stmt}\n{e}")

    conn.commit()
    cur.close()
    conn.close()
    print("votes_count trigger ensured and values recalculated.")


if __name__ == "__main__":
    ensure_votes_count_trigger()
