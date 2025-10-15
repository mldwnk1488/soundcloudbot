from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from core import queue_manager, db_manager
from lang_bot.translations import get_text
from utils import get_user_language_safe, safe_db_operation, format_history_item, send_chunked_message

router = Router()

@router.message(Command("queue"))
async def queue_handler(message: Message):
    user_id = message.from_user.id
    
    try:
        lang = await get_user_language_safe(user_id)
        
        if queue_manager.is_processing():
            queue_size = queue_manager.get_queue_size()
            
            if queue_manager.is_user_in_queue(user_id):
                position = queue_manager.get_queue_position(user_id)
                await message.answer(
                    f"⏳ {get_text(lang, 'you_in_queue')}\n"
                    f"📊 {get_text(lang, 'queue_position')}: {position}\n"
                    f"👥 {get_text(lang, 'total_in_queue')}: {queue_size}\n\n"
                    f"💬 {get_text(lang, 'will_notify_start')}"
                )
            else:
                await message.answer(
                    f"🔄 {get_text(lang, 'processing_now')}\n"
                    f"❌ {get_text(lang, 'not_in_queue')}"
                )
        else:
            if queue_manager.is_user_in_queue(user_id):
                position = queue_manager.get_queue_position(user_id)
                await message.answer(
                    f"⏳ {get_text(lang, 'you_in_queue')}\n"
                    f"📊 {get_text(lang, 'queue_position')}: {position}\n\n"
                    f"🎉 {get_text(lang, 'congrats_first')}"
                )
            else:
                await message.answer(get_text(lang, "queue_empty"))
            
    except Exception as e:
        print(f"Ошибка в queue_handler: {e}")
        lang = await get_user_language_safe(user_id)
        await message.answer(get_text(lang, "error"))

@router.message(Command("history"))
async def history_handler(message: Message):
    user_id = message.from_user.id
    
    try:
        lang = await get_user_language_safe(user_id)
        
        history = await safe_db_operation(
            lambda db: db.get_download_history(user_id),
            fallback=[]
        )
        
        if not history:
            await message.answer(get_text(lang, "no_history"))
            return
        
        text_lines = [f"📋 {get_text(lang, 'history_title')}:\n"]
        
        for i, item in enumerate(history, 1):
            text_lines.extend(await format_history_item(item, lang, i))
        
        full_text = "\n".join(text_lines)
        await send_chunked_message(message.bot, user_id, full_text, lang)
        
    except Exception as e:
        print(f"Ошибка в history_handler: {e}")
        lang = await get_user_language_safe(user_id)
        await message.answer(get_text(lang, "no_history"))

@router.message(Command("stats"))
async def stats_handler(message: Message):
    user_id = message.from_user.id
    
    try:
        lang = await get_user_language_safe(user_id)
        
        user_stats = await safe_db_operation(
            lambda db: db.get_user_statistics(user_id),
            fallback=(0, 0, 0.0)
        )
        
        global_stats = await safe_db_operation(
            lambda db: db.get_global_statistics(),
            fallback=(0, 0, 0, 0.0)
        )
        
        text_lines = [f"📊 {get_text(lang, 'your_stats')}:\n"]
        
        if user_stats and user_stats[0]:
            total_downloads, total_tracks, total_size = user_stats
            text_lines.append(f"• {get_text(lang, 'total_downloads')}: {total_downloads}")
            text_lines.append(f"• {get_text(lang, 'total_tracks')}: {total_tracks}")
            text_lines.append(f"• {get_text(lang, 'total_size')}: {total_size:.1f} MB")
        else:
            text_lines.append(f"• {get_text(lang, 'no_history')}")
        
        text_lines.append("")
        
        if global_stats and global_stats[0]:
            total_users, total_downloads, total_tracks, total_size = global_stats
            text_lines.append(f"🌍 {get_text(lang, 'global_stats')}:")
            text_lines.append(f"• {get_text(lang, 'total_downloads')}: {total_downloads}")
            text_lines.append(f"• {get_text(lang, 'total_tracks')}: {total_tracks}")
            text_lines.append(f"• {get_text(lang, 'total_size')}: {total_size:.1f} MB")
            text_lines.append(f"• {get_text(lang, 'total_users')}: {total_users}")
        else:
            text_lines.append(f"• {get_text(lang, 'no_history')}")
        
        full_text = "\n".join(text_lines)
        await message.answer(full_text)
        
    except Exception as e:
        print(f"Ошибка в stats_handler: {e}")
        lang = await get_user_language_safe(user_id)
        await message.answer(get_text(lang, "error"))

@router.message(Command("status"))
async def status_handler(message: Message):
    user_id = message.from_user.id
    
    try:
        lang = await get_user_language_safe(user_id)
        
        queue_size = queue_manager.get_queue_size()
        is_processing = queue_manager.is_processing()
        
        db = db_manager.get_db()
        db_status = "✅" if db else "❌"
        
        status_text = (
            f"🤖 {get_text(lang, 'status_title')}:\n"
            f"📊 {get_text(lang, 'queue_status')}: {queue_size}\n"
            f"🔄 {get_text(lang, 'processing_status')}: {'✅' if is_processing else '❌'}\n"
            f"🗄️ {get_text(lang, 'database_status')}: {db_status}"
        )
        
        await message.answer(status_text)
        
    except Exception as e:
        print(f"Ошибка в status_handler: {e}")
        lang = await get_user_language_safe(user_id)
        await message.answer(get_text(lang, "error"))