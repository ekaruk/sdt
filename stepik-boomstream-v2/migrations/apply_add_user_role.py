"""
Применение миграции: добавление поля role в таблицу users
"""
import sys
from app.db import engine
from sqlalchemy import text

def apply_migration():
    """Применить SQL миграцию для добавления роли пользователя."""
    
    try:
        with engine.begin() as conn:
            # Проверяем, есть ли уже колонка role
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='role'
            """))
            
            if result.fetchone():
                print("⚠️  Колонка 'role' уже существует в таблице users")
                return
            
            # Добавляем колонку role
            print("Добавление колонки 'role'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN role INTEGER DEFAULT 0 NOT NULL"))
            
            # Создаем индекс
            print("Создание индекса 'idx_users_role'...")
            conn.execute(text("CREATE INDEX idx_users_role ON users(role)"))
        
        print("\n✅ Миграция успешно применена!")
        print("   - Добавлено поле 'role' в таблицу users")
        print("   - Создан индекс idx_users_role")
        print("\nТеперь можно назначить первого админа:")
        print("   UPDATE users SET role = 2 WHERE email = 'your-email@example.com';")
        
    except Exception as e:
        print(f"\n❌ Ошибка при применении миграции: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    apply_migration()
