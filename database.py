import sqlite3
import asyncio
import aiosqlite
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.expanduser("~"), ".music_bot", "bot.db")

class Database:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    async def init_db(self):
        async with aiosqlite.connect(DB_PATH) as db:
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
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    playlist_url TEXT,
                    playlist_title TEXT,
                    tracks_count INTEGER,
                    file_size_mb REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS playlist_cache (
                    playlist_url TEXT PRIMARY KEY,
                    playlist_data TEXT,
                    tracks_data TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action_type TEXT,
                    tracks_count INTEGER,
                    file_size_mb REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
    
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
    
    async def add_download_history(self, user_id, playlist_url, playlist_title, tracks_count, file_size_mb):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                DELETE FROM download_history 
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM download_history 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 4
                )
            ''', (user_id, user_id))
            
            await db.execute('''
                INSERT INTO download_history (user_id, playlist_url, playlist_title, tracks_count, file_size_mb)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, playlist_url, playlist_title, tracks_count, file_size_mb))
            await db.commit()
    
    async def get_download_history(self, user_id, limit=5):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT playlist_url, playlist_title, tracks_count, file_size_mb, created_at
                FROM download_history 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            return await cursor.fetchall()
    
    async def is_playlist_downloaded(self, user_id, playlist_url):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT 1 FROM download_history 
                WHERE user_id = ? AND playlist_url = ? 
                LIMIT 1
            ''', (user_id, playlist_url))
            return await cursor.fetchone() is not None
    
    async def cache_playlist(self, playlist_url, playlist_data, tracks_data):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT OR REPLACE INTO playlist_cache (playlist_url, playlist_data, tracks_data)
                VALUES (?, ?, ?)
            ''', (playlist_url, json.dumps(playlist_data), json.dumps(tracks_data)))
            await db.commit()
    
    async def get_cached_playlist(self, playlist_url):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT playlist_data, tracks_data FROM playlist_cache 
                WHERE playlist_url = ?
            ''', (playlist_url,))
            result = await cursor.fetchone()
            if result:
                return json.loads(result[0]), json.loads(result[1])
            return None, None
    
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
                FROM statistics 
                WHERE user_id = ? AND action_type = 'download'
            ''', (user_id,))
            return await cursor.fetchone()
    
    async def get_global_statistics(self):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(*) as total_downloads,
                    SUM(tracks_count) as total_tracks,
                    SUM(file_size_mb) as total_size
                FROM statistics 
                WHERE action_type = 'download'
            ''')
            return await cursor.fetchone()

    async def get_all_users(self):
        """Получаем всех юзеров для рассылки"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT user_id FROM users')
            users = await cursor.fetchall()
            return [user[0] for user in users]

db = Database()