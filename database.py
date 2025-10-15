import os
import aiosqlite
import json
from datetime import datetime

# 🔥 УМНАЯ БАЗА ДЛЯ RENDER И ЛОКАЛЬНОЙ РАЗРАБОТКИ
if "RENDER" in os.environ:
    # На Render используем /tmp но с персистентностью
    DB_DIR = "/tmp/music_bot"
else:
    # Локально используем домашнюю директорию
    DB_DIR = os.path.join(os.path.expanduser("~"), ".music_bot")

DB_PATH = os.path.join(DB_DIR, "bot.db")

class Database:
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        print(f"📁 База данных: {DB_PATH}")
        print(f"🌍 Окружение: {'Render' if 'RENDER' in os.environ else 'Local'}")
    
    async def init_db(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language TEXT DEFAULT 'ua',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS playlist_cache (
                    playlist_url TEXT PRIMARY KEY,
                    playlist_data TEXT NOT NULL,
                    tracks_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    playlist_url TEXT NOT NULL,
                    playlist_title TEXT NOT NULL,
                    tracks_count INTEGER NOT NULL,
                    file_size_mb REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    tracks_count INTEGER NOT NULL,
                    file_size_mb REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
            print(f"✅ База готова: {DB_PATH}")

    async def add_user(self, user_id, username, first_name, last_name, language='ua'):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, language)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, language))
            await db.commit()

    async def get_user_language(self, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
            result = await cursor.fetchone()
            return result[0] if result else 'ua'

    async def update_user_language(self, user_id, language):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
            await db.commit()

    async def is_playlist_downloaded(self, user_id, playlist_url):
        """🔥 ПРОВЕРЯЕМ СКАЧИВАЛ ЛИ ЮЗЕР ЭТОТ ПЛЕЙЛИСТ РАНЬШЕ"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT playlist_title, created_at FROM download_history 
                WHERE user_id = ? AND playlist_url = ?
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id, playlist_url))
            result = await cursor.fetchone()
            
            if result:
                title, date = result
                return True, title, date
            return False, None, None

    async def get_cached_playlist(self, playlist_url):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT playlist_data, tracks_data FROM playlist_cache 
                WHERE playlist_url = ?
            ''', (playlist_url,))
            result = await cursor.fetchone()
            
            if result:
                playlist_data = json.loads(result[0])
                tracks_data = json.loads(result[1])
                return playlist_data, tracks_data
            return None, None

    async def cache_playlist(self, playlist_url, playlist_data, tracks_data):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT OR REPLACE INTO playlist_cache (playlist_url, playlist_data, tracks_data)
                VALUES (?, ?, ?)
            ''', (playlist_url, json.dumps(playlist_data), json.dumps(tracks_data)))
            await db.commit()

    async def add_download_history(self, user_id, playlist_url, playlist_title, tracks_count, file_size_mb):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT INTO download_history (user_id, playlist_url, playlist_title, tracks_count, file_size_mb)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, playlist_url, playlist_title, tracks_count, file_size_mb))
            await db.commit()

    async def add_statistics(self, user_id, action_type, tracks_count, file_size_mb):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT INTO statistics (user_id, action_type, tracks_count, file_size_mb)
                VALUES (?, ?, ?, ?)
            ''', (user_id, action_type, tracks_count, file_size_mb))
            await db.commit()

    async def get_user_statistics(self, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT 
                    COUNT(*) as total_downloads,
                    SUM(tracks_count) as total_tracks,
                    SUM(file_size_mb) as total_size
                FROM download_history 
                WHERE user_id = ?
            ''', (user_id,))
            result = await cursor.fetchone()
            return result if result else (0, 0, 0.0)

    async def get_download_history(self, user_id, limit=5):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT playlist_url, playlist_title, tracks_count, file_size_mb, created_at
                FROM download_history 
                WHERE user_id = ?
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            results = await cursor.fetchall()
            
            history = []
            for row in results:
                url, title, tracks, size, date = row
                if isinstance(date, str):
                    try:
                        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    except:
                        pass
                history.append((url, title, tracks, size, date))
            
            return history

    async def get_global_statistics(self):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM users')
            total_users = (await cursor.fetchone())[0]
            
            cursor = await db.execute('''
                SELECT 
                    COUNT(*) as total_downloads,
                    SUM(tracks_count) as total_tracks,
                    SUM(file_size_mb) as total_size
                FROM download_history
            ''')
            result = await cursor.fetchone()
            
            total_downloads = result[0] or 0
            total_tracks = result[1] or 0
            total_size = result[2] or 0.0
            
            return (total_users, total_downloads, total_tracks, total_size)

    async def get_all_users(self):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT user_id FROM users')
            results = await cursor.fetchall()
            return [row[0] for row in results]

db = Database()