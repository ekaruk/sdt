"""
Проверка наличия пользователя с telegram_id
"""
from app.db import SessionLocal
from app.models import User

def check_telegram_users():
    db = SessionLocal()
    try:
        users_with_telegram = db.query(User).filter(User.telegram_id.isnot(None)).all()
        
        print(f"\n=== Пользователи с привязанным Telegram ===\n")
        
        if not users_with_telegram:
            print("❌ Нет пользователей с привязанным telegram_id")
            print("\nДля привязки выполните:")
            print("UPDATE users SET telegram_id = YOUR_TELEGRAM_ID WHERE email = 'your@email.com';")
        else:
            for user in users_with_telegram:
                print(f"ID: {user.id}")
                print(f"Email: {user.email}")
                print(f"Telegram ID: {user.telegram_id}")
                print(f"Role: {user.role} ({user.get_role_name()})")
                print(f"Name: {user.first_name} {user.last_name}")
                print("-" * 50)
        
        print(f"\nВсего пользователей с Telegram: {len(users_with_telegram)}\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_telegram_users()
