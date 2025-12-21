"""
Скрипт для получения всех доступных иконок форум-топиков Telegram.
Выводит custom_emoji_id для каждой иконки.
"""

import requests
from app.config import Config

def get_forum_icon_stickers():
    """Получает список всех доступных стикеров для иконок форум-топиков."""
    
    if not Config.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не задан в config!")
        return
    
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getForumTopicIconStickers"
    
    print("🔍 Запрашиваем список иконок для форум-топиков...\n")
    
    try:
        response = requests.get(url)
        
        if not response.ok:
            print(f"❌ Ошибка API: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        
        if not data.get('ok'):
            print(f"❌ API вернул ошибку: {data}")
            return
        
        stickers = data.get('result', [])
        
        if not stickers:
            print("⚠️  Список иконок пуст")
            return
        
        print(f"✅ Найдено {len(stickers)} иконок:\n")
        print("=" * 80)
        
        for i, sticker in enumerate(stickers, 1):
            emoji = sticker.get('emoji', '❓')
            custom_emoji_id = sticker.get('custom_emoji_id', 'N/A')
            file_id = sticker.get('file_id', '')
            
            print(f"{i:2}. {emoji:3} - ID: {custom_emoji_id}")
            
            # Дополнительная информация
            if sticker.get('is_animated'):
                print(f"      (анимированный)")
            if sticker.get('is_video'):
                print(f"      (видео)")
        
        print("=" * 80)
        print(f"\n📝 Для использования в коде:")
        print("FORUM_EMOJI_IDS = {")
        for sticker in stickers:
            emoji = sticker.get('emoji', '❓')
            custom_emoji_id = sticker.get('custom_emoji_id', '')
            print(f"    '{emoji}': '{custom_emoji_id}',")
        print("}")
        
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")


if __name__ == "__main__":
    get_forum_icon_stickers()
