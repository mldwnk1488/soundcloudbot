import asyncio
from database import db

async def test_database():
    print("🧪 Тестируем базу данных...")
    
    # Инициализируем базу
    await db.init_db()
    print("✅ База инициализирована")
    
    # Тест добавления пользователя
    user_id = 123456789
    await db.add_user(user_id, "test_user", "Test", "User", "ua")
    print("✅ Пользователь добавлен")
    
    # Тест получения языка
    lang = await db.get_user_language(user_id)
    print(f"✅ Язык пользователя: {lang}")
    
    # Тест обновления языка
    await db.update_user_language(user_id, "ru")
    lang = await db.get_user_language(user_id)
    print(f"✅ Обновленный язык: {lang}")
    
    # Тест истории загрузок
    await db.add_download_history(user_id, "https://test.com", "Test Playlist", 5, 10.5)
    print("✅ История добавлена")
    
    # Тест получения истории
    history = await db.get_download_history(user_id)
    print(f"✅ История: {history}")
    
    # Тест статистики
    await db.add_statistics(user_id, "download", 5, 10.5)
    print("✅ Статистика добавлена")
    
    user_stats = await db.get_user_statistics(user_id)
    print(f"✅ Статистика пользователя: {user_stats}")
    
    global_stats = await db.get_global_statistics()
    print(f"✅ Глобальная статистика: {global_stats}")
    
    print("🎉 Все тесты пройдены!")

if __name__ == "__main__":
    asyncio.run(test_database())