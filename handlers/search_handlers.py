from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.search import search_engine
from keyboards.main import get_search_keyboard, get_track_selection_keyboard, get_download_keyboard
from lang_bot.translations import get_text
from utils import get_user_language_safe
import asyncio
import logging

logger = logging.getLogger(__name__)

router = Router()

class SearchStates(StatesGroup):
    waiting_for_search_query = State()
    showing_search_results = State()

@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext):
    """Команда для начала поиска"""
    lang = await get_user_language_safe(message.from_user.id)
    
    await message.answer(
        get_text(lang, "search_placeholder"),
        reply_markup=get_search_keyboard(lang)
    )
    await state.set_state(SearchStates.waiting_for_search_query)

@router.callback_query(F.data == "search_tracks")
async def start_search(callback: CallbackQuery, state: FSMContext):
    """Начало поиска по нажатию кнопки"""
    lang = await get_user_language_safe(callback.from_user.id)
    
    await callback.message.edit_text(get_text(lang, "search_placeholder"))
    await state.set_state(SearchStates.waiting_for_search_query)
    await callback.answer()

@router.message(SearchStates.waiting_for_search_query)
async def process_search_query(message: Message, state: FSMContext):
    """Обработка поискового запроса"""
    user_id = message.from_user.id
    query = message.text.strip()
    lang = await get_user_language_safe(user_id)
    
    if len(query) < 2:
        await message.answer(get_text(lang, "search_too_short"))
        return
    
    loading_msg = await message.answer("🔍 Ищу треки...")
    
    try:
        logger.info(f"🔍 Поиск треков для: {query}")
        search_task = asyncio.create_task(search_engine.search_tracks(query, limit=15))
        tracks = await asyncio.wait_for(search_task, timeout=20)
        
        if not tracks:
            await loading_msg.edit_text(get_text(lang, "search_no_results").format(query=query))
            await state.clear()
            return
        
        await state.update_data(search_results=tracks, search_query=query, offset=0)
        
        results_text = format_search_results(tracks[:5], query, lang)
        await loading_msg.edit_text(
            results_text,
            reply_markup=get_track_selection_keyboard(tracks, lang, 0),
            parse_mode="Markdown"
        )
        
        await state.set_state(SearchStates.showing_search_results)
        
    except asyncio.TimeoutError:
        await loading_msg.edit_text(get_text(lang, "search_timeout"))
        await state.clear()
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        await loading_msg.edit_text(get_text(lang, "search_error"))
        await state.clear()

@router.callback_query(F.data.startswith("select_track_"), SearchStates.showing_search_results)
async def select_track(callback: CallbackQuery, state: FSMContext):
    """Выбор трека из результатов поиска"""
    user_id = callback.from_user.id
    track_index = int(callback.data.split("_")[2]) - 1  # Convert to 0-based index
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

@router.callback_query(F.data.startswith("search_"), SearchStates.showing_search_results)
async def navigate_search_results(callback: CallbackQuery, state: FSMContext):
    """Навигация по страницам результатов поиска"""
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

def format_search_results(tracks, query, lang, offset=0):
    """Форматирование результатов поиска"""
    if not tracks:
        return "❌ Ничего не найдено"
    
    text = f"🎵 {get_text(lang, 'search_results').format(query=query)}\n\n"
    
    for i, track in enumerate(tracks, 1):
        track_title = track['title'][:40] + "..." if len(track['title']) > 40 else track['title']
        artist = track['artist'][:20] + "..." if len(track['artist']) > 20 else track['artist']
        
        text += f"**{offset + i}. {track_title}**\n"
        text += f"   👤 {artist} | ⏱ {track['duration_formatted']}\n\n"
    
    total_pages = (len(tracks) + 4) // 5
    current_page = offset // 5 + 1
    
    text += f"📊 {get_text(lang, 'search_found_tracks').format(count=len(tracks))}"
    text += f"\n📄 Страница {current_page}/{total_pages}"
    
    return text