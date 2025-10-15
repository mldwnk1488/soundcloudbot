from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from core import db_manager
from utils import send_message_to_user, get_user_language_safe
import os
import asyncio

router = Router()

ADMIN_ID = int(os.environ.get("ADMIN_ID", "7021944306"))

def is_admin(user_id: int) -> bool:
    if ADMIN_ID == 0:
        print("ADMIN_ID не настроен!")
        return False
    return user_id == ADMIN_ID

@router.message(Command("announce"))
async def announce_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав")
        return
        
    await message.answer("✅ Админка работает!")

@router.message(Command("announce"))
async def announce_handler(message: Message):
    print("ХЕНДЛЕР /announce ВЫЗВАН!")
    user_id = message.from_user.id
    print(f"Юзер {user_id} пытается использовать /announce")
    
    if not is_admin(user_id):
        print("Не админ")
        await message.answer("❌ Не админ")
        return
    
    announcement_text = message.text.replace('/announce', '').strip()
    
    if not announcement_text:
        await message.answer("❌ Напиши текст: /announce ваш_текст")
        return
    
    print(f"Начинаю рассылку: {announcement_text}")
    
    db = db_manager.get_db()
    if not db:
        await message.answer("❌ База данных недоступна")
        return
    
    try:
        users = await db.get_all_users()
        
        if not users:
            await message.answer("❌ Нет пользователей для рассылки")
            return
            
        await message.answer(f"📢 Рассылаю {len(users)} юзерам...")
        
        success = 0
        failed = 0
        blocked = 0
        
        for user_id in users:
            print(f"Отправляю юзеру {user_id}")
            try:
                user_lang = await get_user_language_safe(user_id)
                personalized_text = f"📢 {get_announcement_header(user_lang)}:\n\n{announcement_text}"
                
                await send_message_to_user(message.bot, user_id, personalized_text, user_lang)
                success += 1
                print(f"✅ Отправлено юзеру {user_id}")
                
                if success % 10 == 0:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                error_msg = str(e).lower()
                if "blocked" in error_msg or "bot was blocked" in error_msg:
                    blocked += 1
                    print(f"🚫 Юзер {user_id} заблокировал бота")
                else:
                    failed += 1
                    print(f"❌ Не удалось отправить {user_id}: {e}")
        
        report = f"✅ Рассылка завершена!\n\n"
        report += f"• Успешно: {success}\n"
        report += f"• Не удалось: {failed}\n"
        report += f"• Заблокировали бота: {blocked}\n"
        report += f"• Всего: {len(users)}"
        
        await message.answer(report)
        
    except Exception as e:
        print(f"Критическая ошибка рассылки: {e}")
        await message.answer(f"❌ Ошибка рассылки: {e}")

@router.message(Command("stats_full"))
async def full_stats_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Не админ")
        return
    
    db = db_manager.get_db()
    if not db:
        await message.answer("❌ База данных недоступна")
        return
    
    try:
        global_stats = await db.get_global_statistics()
        
        if not global_stats:
            await message.answer("❌ Нет данных статистики")
            return
            
        total_users, total_downloads, total_tracks, total_size = global_stats
        
        stats_text = "📊 **ПОЛНАЯ СТАТИСТИКА БОТА**\n\n"
        stats_text += f"👥 **Пользователей:** {total_users}\n"
        stats_text += f"📥 **Загрузок:** {total_downloads}\n" 
        stats_text += f"🎵 **Треков:** {total_tracks}\n"
        stats_text += f"💾 **Общий размер:** {total_size:.1f} MB\n\n"
        
        if total_users > 0:
            avg_downloads = total_downloads / total_users
            avg_tracks = total_tracks / total_users
            avg_size = total_size / total_users
            
            stats_text += f"📈 **Средние показатели на пользователя:**\n"
            stats_text += f"• Загрузок: {avg_downloads:.1f}\n"
            stats_text += f"• Треков: {avg_tracks:.1f}\n"
            stats_text += f"• Размер: {avg_size:.1f} MB\n"
        
        await message.answer(stats_text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        await message.answer(f"❌ Ошибка: {e}")

@router.message(Command("cleanup"))
async def cleanup_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Не админ")
        return
        
    await message.answer("🧹 Очистка кэша... (в разработке)")

def get_announcement_header(lang: str) -> str:
    headers = {
        "ua": "ОГОЛОШЕННЯ",
        "ru": "ОБЪЯВЛЕНИЕ", 
        "en": "ANNOUNCEMENT"
    }
    return headers.get(lang, headers["ua"])