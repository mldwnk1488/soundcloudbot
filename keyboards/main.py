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
    """Клавиатура для выбора трека из результатов поиска"""
    buttons = []
    
    for i, track in enumerate(tracks[offset:offset+5], 1):
        track_title = track['title'][:30] + "..." if len(track['title']) > 30 else track['title']
        button_text = f"{offset + i}. {track_title} - {track['artist']}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"select_track_{track['id']}")])
    
    # Кнопки навигации
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"search_prev_{offset-5}"))
    
    if offset + 5 < len(tracks):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"search_next_{offset+5}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="search_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)