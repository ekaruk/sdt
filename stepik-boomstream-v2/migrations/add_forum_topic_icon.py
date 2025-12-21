"""
Миграция: добавление поля forum_topic_icon в таблицу stepik_modules
"""

from app.db import SessionLocal, engine
from sqlalchemy import text

def apply_migration():
    """Добавляет колонку forum_topic_icon в таблицу stepik_modules"""
    
    db = SessionLocal()
    
    try:
        # Проверяем существует ли уже колонка
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='stepik_modules' 
            AND column_name='forum_topic_icon'
        """))
        
        if result.fetchone():
            print("✅ Колонка forum_topic_icon уже существует")
            return
        
        # Добавляем колонку
        db.execute(text("""
            ALTER TABLE stepik_modules 
            ADD COLUMN forum_topic_icon VARCHAR
        """))
        
        db.commit()
        print("✅ Миграция add_forum_topic_icon применена успешно!")
        print("   Добавлена колонка forum_topic_icon в таблицу stepik_modules")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка применения миграции: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Применение миграции: add_forum_topic_icon")
    apply_migration()
