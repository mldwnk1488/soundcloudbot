# main_bot.py
import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКА =====
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        print("🔍 Найден .env файл")
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден!")
    exit(1)

# ===== СОСТОЯНИЯ =====
class SearchStates(StatesGroup):
    waiting_query = State()
    showing_results = State()

# ===== ГЛАВНЫЙ РОУТЕР =====
main_router = Router()

# ===== ИМПОРТЫ ДЛЯ ФУНКЦИОНАЛА =====
async def import_handlers():
    """Импортируем все необходимые модули"""
    global search_engine, db
    try:
        from services.search import search_engine
        from database import db
        from core import db_manager
        from utils import get_user_language_safe
        from lang_bot.translations import get_text
        return True
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        return False

# ===== КЛАВИАТУРЫ =====
def get_search_keyboard(language="ua"):
    from lang_bot.translations import get_text
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск треков", callback_data="search_tracks")]
    ])

def get_track_selection_keyboard(tracks, language="ua", offset=0):
    from lang_bot.translations import get_text
    
    buttons = []
    displayed_tracks = tracks[offset:offset+5]
    
    for i, track in enumerate(displayed_tracks, 1):
        track_title = track['title'][:30] + "..." if len(track['title']) > 30 else track['title']
        button_text = f"{offset + i}. {track_title}"
        buttons.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"select_track_{offset + i}"
        )])
    
    nav_buttons = []
    total_pages = (len(tracks) + 4) // 5
    
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(
            text=f"⬅️ {get_text(language, 'prev_page')}", 
            callback_data=f"search_prev"
        ))
    
    if offset + 5 < len(tracks):
        nav_buttons.append(InlineKeyboardButton(
            text=f"{get_text(language, 'next_page')} ➡️", 
            callback_data=f"search_next"
        ))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(
        text=f"❌ {get_text(language, 'canceled')}", 
        callback_data="search_cancel"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_download_keyboard(language="ua"):
    from lang_bot.translations import get_text
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(language, "download_zip"), callback_data="download_zip")],
        [InlineKeyboardButton(text=get_text(language, "download_tracks"), callback_data="download_tracks")]
    ])

# ===== ФОРМАТИРОВАНИЕ РЕЗУЛЬТАТОВ =====
def format_search_results(tracks, query, lang, offset=0):
    from lang_bot.translations import get_text
    
    if not tracks:
        return f"❌ {get_text(lang, 'search_no_results').format(query=query)}"
    
    text = f"🎵 {get_text(lang, 'search_results').format(query=query)}\n\n"
    page_tracks = tracks[offset:offset+5]
    
    for i, track in enumerate(page_tracks, 1):
        track_title = track['title'][:40] + "..." if len(track['title']) > 40 else track['title']
        artist = track['artist'][:25] + "..." if len(track['artist']) > 25 else track['artist']
        
        if artist == get_text(lang, "unknown_artist"):
            text += f"**{offset + i}. {track_title}**\n"
        else:
            text += f"**{offset + i}. {track_title}**\n"
            text += f"   👤 {artist} | ⏱ {track['duration_formatted']}\n\n"
    
    total_pages = (len(tracks) + 4) // 5
    current_page = offset // 5 + 1
    
    text += f"📊 {get_text(lang, 'tracks_found')}: {len(tracks)}"
    text += f"\n📄 {get_text(lang, 'search_page')} {current_page}/{total_pages}"
    
    return text

# ===== ОСНОВНЫЕ КОМАНДЫ =====
@main_router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    """Команда start с выбором языка"""
    try:
        from handlers.start import start_handler
        await start_handler(message, state)
    except Exception as e:
        logger.error(f"❌ Ошибка start: {e}")
        await message.answer("🚀 Бот запущен! Используй /search для поиска музыки")

@main_router.message(Command("search"))
async def search_command(message: Message, state: FSMContext):
    """Поиск музыки"""
    if not await import_handlers():
        await message.answer("❌ Сервис временно недоступен")
        return
        
    from utils import get_user_language_safe
    from lang_bot.translations import get_text
    
    lang = await get_user_language_safe(message.from_user.id)
    
    await message.answer(
        get_text(lang, "search_placeholder"),
        reply_markup=get_search_keyboard(lang)
    )
    await state.set_state(SearchStates.waiting_query)

@main_router.callback_query(F.data == "search_tracks")
async def start_search_callback(callback: CallbackQuery, state: FSMContext):
    """Кнопка начала поиска"""
    if not await import_handlers():
        await callback.answer("❌ Сервис временно недоступен", show_alert=True)
        return
        
    from utils import get_user_language_safe
    from lang_bot.translations import get_text
    
    lang = await get_user_language_safe(callback.from_user.id)
    
    await callback.message.edit_text(get_text(lang, "search_placeholder"))
    await state.set_state(SearchStates.waiting_query)
    await callback.answer()

# ===== ОБРАБОТКА ПОИСКОВОГО ЗАПРОСА =====
@main_router.message(SearchStates.waiting_query)
async def process_search_query(message: Message, state: FSMContext):
    """Обработка поискового запроса"""
    if not await import_handlers():
        await message.answer("❌ Сервис временно недоступен")
        return
        
    from utils import get_user_language_safe
    from lang_bot.translations import get_text
    import asyncio
    
    user_id = message.from_user.id
    query = message.text.strip()
    lang = await get_user_language_safe(user_id)
    
    if len(query) < 2:
        await message.answer(get_text(lang, "search_too_short"))
        return
    
    loading_msg = await message.answer(get_text(lang, "search_loading_improved"))
    
    try:
        tracks = await search_engine.search_tracks(query, limit=25)
        
        if not tracks:
            await loading_msg.edit_text(get_text(lang, "search_no_results").format(query=query))
            await state.clear()
            return
        
        if len(tracks) > 5:
            await loading_msg.edit_text(get_text(lang, "search_more_results"))
        
        await state.update_data(
            search_results=tracks, 
            search_query=query, 
            offset=0
        )
        
        results_text = format_search_results(tracks[:5], query, lang)
        await loading_msg.edit_text(
            results_text,
            reply_markup=get_track_selection_keyboard(tracks, lang, 0),
            parse_mode="Markdown"
        )
        
        await state.set_state(SearchStates.showing_results)
        
    except asyncio.TimeoutError:
        await loading_msg.edit_text(get_text(lang, "search_timeout"))
        await state.clear()
    except Exception as e:
        logger.error(f"❌ Ошибка поиска: {e}")
        await loading_msg.edit_text(get_text(lang, "search_error"))
        await state.clear()

# ===== НАВИГАЦИЯ ПО РЕЗУЛЬТАТАМ =====
@main_router.callback_query(F.data.startswith("search_"), SearchStates.showing_results)
async def navigate_search_results(callback: CallbackQuery, state: FSMContext):
    """Навигация по страницам результатов"""
    if not await import_handlers():
        await callback.answer("❌ Сервис временно недоступен", show_alert=True)
        return
        
    from utils import get_user_language_safe
    from lang_bot.translations import get_text
    
    user_data = await state.get_data()
    tracks = user_data.get('search_results', [])
    query = user_data.get('search_query', '')
    current_offset = user_data.get('offset', 0)
    lang = await get_user_language_safe(callback.from_user.id)
    
    action = callback.data.split('_')[1]
    
    if action == 'prev':
        new_offset = max(0, current_offset - 5)
    elif action == 'next':
        new_offset = min(len(tracks) - 5, current_offset + 5)
    elif action == 'cancel':
        await callback.message.delete()
        await state.clear()
        await callback.answer()
        return
    else:
        await callback.answer()
        return
    
    await state.update_data(offset=new_offset)
    
    results_text = format_search_results(tracks[new_offset:new_offset+5], query, lang, new_offset)
    await callback.message.edit_text(
        results_text,
        reply_markup=get_track_selection_keyboard(tracks, lang, new_offset),
        parse_mode="Markdown"
    )
    
    await callback.answer()

# ===== ВЫБОР ТРЕКА =====
@main_router.callback_query(F.data.startswith("select_track_"), SearchStates.showing_results)
async def select_track_callback(callback: CallbackQuery, state: FSMContext):
    """Выбор трека из результатов"""
    if not await import_handlers():
        await callback.answer("❌ Сервис временно недоступен", show_alert=True)
        return
        
    from utils import get_user_language_safe
    from lang_bot.translations import get_text
    
    user_id = callback.from_user.id
    track_index = int(callback.data.split("_")[2]) - 1
    lang = await get_user_language_safe(user_id)
    
    user_data = await state.get_data()
    tracks = user_data.get('search_results', [])
    
    if track_index < 0 or track_index >= len(tracks):
        await callback.answer(get_text(lang, "error"), show_alert=True)
        return
    
    selected_track = tracks[track_index]
    
    await state.update_data({
        'url': selected_track['permalink_url'],
        'content_type': 'track',
        'playlist_title': selected_track['title'],
        'track_count': 1,
        'artist': selected_track['artist']
    })
    
    await callback.message.edit_text(
        f"🎵 **{get_text(lang, 'track')}**\n"
        f"📀 **{get_text(lang, 'title')}:** {selected_track['title']}\n"
        f"👤 **{get_text(lang, 'artist')}:** {selected_track['artist']}\n"
        f"⏱ **{get_text(lang, 'duration')}:** {selected_track['duration_formatted']}\n\n"
        f"{get_text(lang, 'choose_format')}",
        parse_mode="Markdown",
        reply_markup=get_download_keyboard(lang)
    )
    
    await state.set_state(None)
    await callback.answer()

# ===== СКАЧИВАНИЕ =====
@main_router.callback_query(F.data.in_(["download_zip", "download_tracks"]))
async def download_selected_track(callback: CallbackQuery, state: FSMContext):
    """Скачивание выбранного трека"""
    try:
        from handlers.download import callback_download
        await callback_download(callback, state)
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания: {e}")
        await callback.answer("❌ Ошибка при скачивании", show_alert=True)

@main_router.message(F.text.startswith(('http://', 'https://', 'soundcloud.com/')))
async def handle_soundcloud_url(message: Message, state: FSMContext):
    """Обработка SoundCloud ссылок"""
    try:
        from handlers.download import playlist_handler
        await playlist_handler(message, state)
    except Exception as e:
        logger.error(f"❌ Ошибка обработки ссылки: {e}")
        await message.answer("❌ Ошибка при обработке ссылки")

# ===== ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ =====
@main_router.message(Command("help"))
async def help_cmd(message: Message):
    """Помощь"""
    if not await import_handlers():
        await message.answer("ℹ️ Бот для поиска и скачивания музыки с SoundCloud")
        return
        
    from utils import get_user_language_safe
    from lang_bot.translations import get_text
    
    lang = await get_user_language_safe(message.from_user.id)
    await message.answer(get_text(lang, "main_text"))

@main_router.message(Command("stats"))
async def stats_cmd(message: Message):
    """Статистика"""
    try:
        from handlers.queue import stats_handler
        await stats_handler(message)
    except Exception as e:
        logger.error(f"❌ Ошибка stats: {e}")
        await message.answer("📊 Статистика скоро будет доступна")

@main_router.message(Command("history"))
async def history_cmd(message: Message):
    """История"""
    try:
        from handlers.queue import history_handler
        await history_handler(message)
    except Exception as e:
        logger.error(f"❌ Ошибка history: {e}")
        await message.answer("📋 История скоро будет доступна")

# ===== CALLBACK ОБРАБОТЧИКИ =====
@main_router.callback_query(F.data.startswith("lang_"))
async def language_callback(callback: CallbackQuery, state: FSMContext):
    """Выбор языка"""
    try:
        from handlers.start import select_language
        await select_language(callback, state)
    except Exception as e:
        logger.error(f"❌ Ошибка выбора языка: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@main_router.callback_query(F.data.startswith("agree_"))
async def agreement_callback(callback: CallbackQuery, state: FSMContext):
    """Соглашение"""
    try:
        from handlers.start import process_agreement
        await process_agreement(callback, state)
    except Exception as e:
        logger.error(f"❌ Ошибка соглашения: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@main_router.callback_query(F.data == "subscribed")
async def subscribed_callback(callback: CallbackQuery):
    """Подписка"""
    try:
        from handlers.start import callback_subscribed
        await callback_subscribed(callback)
    except Exception as e:
        logger.error(f"❌ Ошибка подписки: {e}")
        await callback.answer("Спасибо!", show_alert=True)

# ===== ЗАПУСК БОТА =====
async def setup_database():
    """Настройка базы данных"""
    try:
        from database import db
        from core import db_manager
        await db.init_db()
        db_manager.set_db(db)
        logger.info("✅ База данных готова")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка базы данных: {e}")
        return False

async def main():
    logger.info("🚀 Запускаю полнофункционального бота...")
    
    if not await setup_database():
        logger.warning("⚠️ База данных не настроена, некоторые функции могут не работать")
    
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(main_router)
    
    logger.info("🎵 SoundCloud Бот готов!")
    logger.info("🔍 Команды: /start, /search, /help, /stats, /history")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")