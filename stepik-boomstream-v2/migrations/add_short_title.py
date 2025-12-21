"""
Миграция: Добавление короткого названия для модулей
"""
from app.db import SessionLocal
from app.models import StepikModule
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # Добавляем колонку (если еще не существует)
        print("Adding short_title column...")
        db.execute(text("ALTER TABLE stepik_modules ADD COLUMN IF NOT EXISTS short_title VARCHAR"))
        db.commit()
        
        # Обновляем существующие записи
        print("Updating existing modules with short titles...")
        
        short_titles = {
            561993: "Раздел 1",
            579296: "Раздел 2", 
            564649: "Раздел 3",
            579297: "Раздел 4",
            611382: "Раздел 5",
            611383: "Раздел 6"
        }
        
        for module_id, short_title in short_titles.items():
            module = db.query(StepikModule).filter_by(id=module_id).first()
            if module:
                module.short_title = short_title
                print(f"  ✓ {module.title} → {short_title}")
        
        db.commit()
        print("\n✅ Migration completed successfully!")
        
        # Показываем результат
        print("\nCurrent modules:")
        modules = db.query(StepikModule).order_by(StepikModule.position).all()
        for m in modules:
            print(f"  {m.id}: {m.short_title or '(no short title)'} - {m.title}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
