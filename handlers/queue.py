from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from services.queue_manager import queue_manager
from lang_bot.translations import get_text
from bot_data import get_db  # <-- ДОБАВИЛ

router = Router()

@router.message(Command("queue"))
async def queue_handler(message: Message):
    user_id = message.from_user.id
    
    db = get_db()  # <-- ИСПРАВИЛ
    lang = await db.get_user_language(user_id)
    
    if user_id in queue_manager.queue_status:
        pos = queue_manager.get_queue_position(user_id)
        if pos > 0:
            await message.answer(
                f"📊 {get_text(lang, 'your_queue_number')}: {pos}\n"
                f"{get_text(lang, 'total_in_queue')}: {len(queue_manager.download_queue)}"
            )
        else:
            await message.answer(get_text(lang, "processing_now"))
    else:
        await message.answer(get_text(lang, "not_in_queue"))

@router.message(Command("history"))
async def history_handler(message: Message):
    user_id = message.from_user.id
    
    db = get_db()  # <-- ИСПРАВИЛ
    lang = await db.get_user_language(user_id)
    
    history = await db.get_download_history(user_id)
    
    if not history:
        await message.answer("📭 История загрузок пуста")
        return
    
    text = "📋 Последние загрузки:\n\n"
    for item in history:
        url, title, tracks, size, date = item
        date_str = date.strftime("%d.%m.%Y %H:%M") if hasattr(date, 'strftime') else str(date)[:16]
        
        text += f"• {title}\n"
        text += f"  🎵 {tracks} треков, 💾 {size:.1f}MB\n"
        text += f"  📅 {date_str}\n\n"
    
    await message.answer(text)

@router.message(Command("stats"))
async def stats_handler(message: Message):
    user_id = message.from_user.id
    
    db = get_db()  # <-- ИСПРАВИЛ
    lang = await db.get_user_language(user_id)
    
    user_stats = await db.get_user_statistics(user_id)
    
    text = "📊 Ваша статистика:\n\n"
    
    if user_stats and user_stats[0]:
        total_downloads, total_tracks, total_size = user_stats
        text += f"• Загрузок: {total_downloads}\n"
        text += f"• Треков: {total_tracks}\n"
        text += f"• Общий размер: {total_size:.1f} MB\n\n"
    else:
        text += "• Нет данных о загрузках\n\n"
    
    global_stats = await db.get_global_statistics()
    if global_stats and global_stats[0]:
        total_users, total_downloads, total_tracks, total_size = global_stats
        text += f"🌍 Общая статистика бота:\n"
        text += f"• Пользователей: {total_users}\n"
        text += f"• Загрузок: {total_downloads}\n"
        text += f"• Треков: {total_tracks}\n"
        text += f"• Размер: {total_size:.1f} MB"
    
    await message.answer(text)