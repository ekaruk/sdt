"""
Проверка структуры таблицы users
"""
from app.db import engine
from sqlalchemy import inspect

def check_users_table():
    """Показать все колонки таблицы users."""
    
    inspector = inspect(engine)
    
    print("\n=== Структура таблицы USERS ===\n")
    
    columns = inspector.get_columns('users')
    
    print(f"{'Column':<20} {'Type':<20} {'Nullable':<10} {'Default'}")
    print("-" * 70)
    
    for col in columns:
        col_name = col['name']
        col_type = str(col['type'])
        nullable = 'YES' if col['nullable'] else 'NO'
        default = col.get('default', '-')
        
        print(f"{col_name:<20} {col_type:<20} {nullable:<10} {default}")
    
    print("\n" + "=" * 70)
    
    # Проверяем индексы
    print("\n=== Индексы таблицы USERS ===\n")
    indexes = inspector.get_indexes('users')
    
    if indexes:
        for idx in indexes:
            print(f"- {idx['name']}: {idx['column_names']}")
    else:
        print("Нет индексов")
    
    print()

if __name__ == "__main__":
    check_users_table()
