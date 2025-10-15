from aiogram import Bot
from aiogram.types import FSInputFile
from config import AD_MESSAGE
from keyboards.main import get_ad_keyboard
from lang_bot.translations import get_text
from core import db_manager

async def send_message_to_user(bot: Bot, user_id: int, text: str, lang=None):
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        if lang is None:
            lang = await get_user_language_safe(user_id)
        error_text = get_text(lang, "failed_send_message")
        print(f"{error_text} {user_id}: {e}")

async def send_document_to_user(bot: Bot, user_id: int, document, caption: str = "", lang=None):
    try:
        await bot.send_document(user_id, document, caption=caption)
    except Exception as e:
        if lang is None:
            lang = await get_user_language_safe(user_id)
        error_text = get_text(lang, "failed_send_document")
        print(f"{error_text} {user_id}: {e}")

async def send_ad_message(bot: Bot, user_id: int, lang: str = "ua"):
    try:
        await bot.send_message(
            user_id,
            AD_MESSAGE.get(lang, AD_MESSAGE["ua"]),
            reply_markup=get_ad_keyboard(lang),
            parse_mode="Markdown"
        )
    except Exception as e:
        if lang is None:
            lang = await get_user_language_safe(user_id)
        error_text = get_text(lang, "failed_send_ad")
        print(f"{error_text} {user_id}: {e}")

async def safe_delete_message(bot: Bot, chat_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

async def get_user_language_safe(user_id: int) -> str:
    try:
        db = db_manager.get_db()
        if db:
            return await db.get_user_language(user_id)
    except Exception as e:
        print(f"Ошибка получения языка пользователя {user_id}: {e}")
    
    return 'ua'

def is_valid_url(text):
    if not text or not isinstance(text, str):
        return False
    
    text = text.strip()
    valid_starts = ('http://', 'https://', 'soundcloud.com/')
    
    if not any(text.startswith(start) for start in valid_starts):
        return False
    
    if ' ' in text or '\n' in text:
        return False
        
    return True

async def safe_db_operation(operation, fallback=None):
    """Универсальная функция для безопасных операций с БД"""
    try:
        db = db_manager.get_db()
        if db:
            return await operation(db)
        return fallback
    except Exception as e:
        print(f"Ошибка операции с БД: {e}")
        return fallback

async def format_history_item(item, lang, index):
    """Форматирование элемента истории"""
    url, title, tracks, size, date = item
    
    date_str = get_text(lang, "unknown")
    if hasattr(date, 'strftime'):
        date_str = date.strftime("%d.%m.%Y %H:%M")
    elif isinstance(date, str):
        date_str = date[:16]
    
    clean_title = title[:50] + "..." if len(title) > 50 else title
    
    return [
        f"{index}. **{clean_title}**",
        f"   🎵 {tracks} {get_text(lang, 'track')}, 💾 {size:.1f}MB",
        f"   📅 {date_str}",
        ""
    ]

async def send_chunked_message(bot: Bot, user_id: int, text: str, lang=None, max_length=4096):
    """Отправка длинных сообщений частями"""
    if len(text) <= max_length:
        await send_message_to_user(bot, user_id, text, lang)
        return
    
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line
    
    if current_chunk:
        chunks.append(current_chunk)
    
    for i, chunk in enumerate(chunks):
        prefix = f"📄 Часть {i+1}/{len(chunks)}\n\n" if len(chunks) > 1 else ""
        await send_message_to_user(bot, user_id, prefix + chunk, lang)