import os
import aiosqlite
import json
from datetime import datetime

# 🔥 ИСПОЛЬЗУЕМ /tmp ДЛЯ СОХРАНЕНИЯ МЕЖДУ ДЕПЛОЯМИ
DB_PATH = os.path.join("/tmp", "bot.db")

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
            await db.commit()
            print(f"✅ База создана в {DB_PATH}")
    
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

db = Database()