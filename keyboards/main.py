from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from lang_bot.translations import get_text

def get_download_keyboard(language="ua"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(language, "download_zip"), callback_data="download_zip")],
        [InlineKeyboardButton(text=get_text(language, "download_tracks"), callback_data="download_tracks")]
    ])

def get_ad_keyboard(language="ua"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(language, "my_channel"), url="https://t.me/+qjlekyqElLtkYTcy")],
        [InlineKeyboardButton(text=get_text(language, "already_subscribed"), callback_data="subscribed")]
    ])

def get_download_keyboard(language="ua"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(language, "download_zip"), callback_data="download_zip")],
        [InlineKeyboardButton(text=get_text(language, "download_tracks"), callback_data="download_tracks")]
    ])

def get_ad_keyboard(language="ua"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(language, "my_channel"), url="https://t.me/+qjlekyqElLtkYTcy")],
        [InlineKeyboardButton(text=get_text(language, "already_subscribed"), callback_data="subscribed")]
    ])

def get_search_keyboard(language="ua"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск треков", callback_data="search_tracks")]
    ])

def get_track_selection_keyboard(tracks, language="ua", offset=0):
    """Клавиатура для выбора трека с переводами"""
    from lang_bot.translations import get_text
    
    buttons = []
    
    # Показываем только 5 треков на странице
    displayed_tracks = tracks[offset:offset+5]
    
    for i, track in enumerate(displayed_tracks, 1):
        track_title = track['title'][:30] + "..." if len(track['title']) > 30 else track['title']
        button_text = f"{offset + i}. {track_title}"
        buttons.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"select_track_{offset + i}"
        )])
    
    # Кнопки навигации с переводами
    nav_buttons = []
    
    total_pages = (len(tracks) + 4) // 5
    current_page = offset // 5 + 1
    
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