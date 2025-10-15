import sqlite3
import os

DB_PATH = os.path.expanduser("~/.music_bot/bot.db")

def check_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("📊 СТАТИСТИКА БАЗЫ:\n")
    
    # Юзеры
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]
    print(f"👥 Юзеров: {users_count}")
    
    # Загрузки
    cursor.execute("SELECT COUNT(*) FROM download_history")
    downloads_count = cursor.fetchone()[0]
    print(f"📥 Загрузок: {downloads_count}")
    
    # Статистика
    cursor.execute("SELECT SUM(tracks_count), SUM(file_size_mb) FROM statistics")
    tracks, size = cursor.fetchone()
    print(f"🎵 Треков: {tracks or 0}")
    print(f"💾 Размер: {size or 0:.1f} MB")
    
    print(f"\n📋 Последние загрузки:")
    cursor.execute("""
        SELECT user_id, playlist_title, tracks_count, file_size_mb, created_at 
        FROM download_history 
        ORDER BY created_at DESC 
        LIMIT 3
    """)
    
    for row in cursor.fetchall():
        user_id, title, tracks, size, date = row
        print(f"• {title} ({tracks} треков, {size:.1f}MB)")
    
    conn.close()

if __name__ == "__main__":
    check_db()