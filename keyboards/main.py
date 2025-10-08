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