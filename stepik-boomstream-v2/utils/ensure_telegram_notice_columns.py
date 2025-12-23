import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import engine


def _column_exists(conn, column_name: str) -> bool:
    result = conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'telegram_topics'
              AND column_name = :column_name
            """
        ),
        {"column_name": column_name},
    )
    return result.first() is not None


def ensure_telegram_notice_columns() -> None:
    with engine.begin() as conn:
        if not _column_exists(conn, "notice_message_id"):
            conn.execute(
                text("ALTER TABLE telegram_topics ADD COLUMN notice_message_id INTEGER")
            )
            print("notice_message_id column added.")
        else:
            print("notice_message_id column already exists.")

        if not _column_exists(conn, "notice_is_pinned"):
            conn.execute(
                text(
                    "ALTER TABLE telegram_topics "
                    "ADD COLUMN notice_is_pinned BOOLEAN NOT NULL DEFAULT false"
                )
            )
            print("notice_is_pinned column added.")
        else:
            print("notice_is_pinned column already exists.")


if __name__ == "__main__":
    ensure_telegram_notice_columns()
