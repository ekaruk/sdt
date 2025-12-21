#!/usr/bin/env python
import sys
import json
import datetime
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy import DateTime, Date, Time, Integer, BigInteger

# Добавляем корневую папку проекта в sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Config

#"Использование:\n"
#              $env:DATABASE_URL = "sqlite:///local.db"
#            "  python dump_load.py export dump.json\n"
#            "  python dump_load.py import dump.json [--truncate]\n"


# ---------- утилиты подключения к БД ----------

def get_engine() -> Engine:
    """
    Создаёт SQLAlchemy Engine на основе Config.DATABASE_URL.
    Поддерживаются sqlite, postgresql и др.
    """
    db_url = Config.DATABASE_URL
    if not db_url:
        raise RuntimeError("DATABASE_URL не задан в конфигурации")
    return create_engine(db_url, pool_pre_ping=True)


@contextmanager
def db_conn(engine: Engine):
    """
    Контекстный менеджер: открывает соединение и транзакцию,
    коммитит при успешном завершении и откатывает при ошибке.
    """
    conn = engine.connect()
    trans = conn.begin()
    try:
        yield conn
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()


# ---------- сериализация значений для JSON ----------

def serialize_value(value):
    """
    Преобразует значения в JSON-совместимый вид.
    datetime/date/time → ISO-строка.
    Остальное возвращаем как есть.
    """
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    return value


def deserialize_value(column, value):
    """
    Convert JSON-loaded values back into Python objects expected by SQLAlchemy
    for DateTime/Date/Time columns.
    """
    if value is None:
        return None

    col_type = column.type
    if isinstance(col_type, DateTime):
        return datetime.datetime.fromisoformat(value)
    if isinstance(col_type, Date):
        return datetime.date.fromisoformat(value)
    if isinstance(col_type, Time):
        return datetime.time.fromisoformat(value)
    
    # ЧИСЛА (Integer / BigInteger)
    if isinstance(col_type, (Integer, BigInteger)):
        if isinstance(value, str) and value.strip() == "":
            return None
        if isinstance(value, str):
            return int(value)
        return value
    
    return value


# ---------- экспорт ----------

def export_db(filename: str):
    """
    Выгружает ВСЮ базу в JSON-файл.

    Формат:
    {
      "table_name_1": [ {col: val, ...}, ... ],
      "table_name_2": [ ... ]
    }

    - Схему читаем из самой БД через MetaData().reflect()
    - Для каждой таблицы берём все строки, значения
      datetime/date/time превращаем в строки.
    """
    engine = get_engine()
    metadata = MetaData()
    metadata.reflect(bind=engine)

    data = {}

    with db_conn(engine) as conn:
        # sorted_tables — в порядке с учётом внешних ключей (родители раньше)
        for table in metadata.sorted_tables:
            rows = conn.execute(table.select()).mappings().all()

            processed_rows = []
            for row in rows:
                converted = {
                    key: serialize_value(value)
                    for key, value in row.items()
                }
                processed_rows.append(converted)

            data[table.name] = processed_rows

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Экспорт завершён. Файл: {filename}")


# ---------- импорт ----------

def import_db(filename: str, truncate: bool = False):
    """
    Импортирует данные из JSON-файла в БД.

    Ожидаемый формат JSON — такой же, как у export_db().

    Поведение:
    - Читает JSON: { "table": [ {...}, {...} ], ... }
    - Отражает актуальную схему БД через MetaData.reflect()
    - Если truncate=True:
        * очищает таблицы в обратном порядке зависимостей
          (сначала дочерние, потом родительские)
    - Для каждой таблицы из JSON:
        * берёт список существующих колонок
        * фильтрует словари так, чтобы остались только реально существующие поля
        * вставляет данные (bulk insert)
      → Таким образом, если в дампе есть столбец, которого уже нет в схеме,
        он просто игнорируется.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Файл {filename} не найден")

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    engine = get_engine()
    metadata = MetaData()
    metadata.reflect(bind=engine)

    with db_conn(engine) as conn:
        if truncate:
            # Удаляем данные из таблиц в обратном порядке (дети → родители),
            # чтобы не было конфликтов по внешним ключам.
            for table in reversed(metadata.sorted_tables):
                if table.name in data:
                    conn.execute(table.delete())

        # Вставляем данные в прямом порядке (родители → дети)
        for table in metadata.sorted_tables:
            table_name = table.name
            if table_name not in data:
                continue

            rows = data[table_name]
            if not rows:
                continue

            # Список реальных колонок в таблице
            existing_cols = {col.name for col in table.columns}

            filtered_rows = []
            for row in rows:
                # Берём только те ключи, которые реально существуют в таблице
                filtered = {}
                for k, v in row.items():
                    if k in existing_cols:
                        column = table.columns[k]
                        filtered[k] = deserialize_value(column, v)
                if filtered:
                    filtered_rows.append(filtered)

            if filtered_rows:
                conn.execute(table.insert(), filtered_rows)

    print(f"✅ Импорт завершён из {filename}")


# ---------- CLI ----------

def main():
    if len(sys.argv) < 3:
        print(
            "Использование:\n"
            "  python dump_load.py export dump.json\n"
            "  python dump_load.py import dump.json [--truncate]\n"
        )
        sys.exit(1)

    cmd = sys.argv[1]
    filename = sys.argv[2]
    truncate = "--truncate" in sys.argv[3:]

    if cmd == "export":
        export_db(filename)
    elif cmd == "import":
        import_db(filename, truncate=truncate)
    else:
        print("Неизвестная команда. Используй 'export' или 'import'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
