from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_download_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="скачать архивом", callback_data="download_zip")],
        [InlineKeyboardButton(text="скачать треки сюда", callback_data="download_tracks")]
    ])

def get_ad_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="мой тгк", url="https://t.me/+qjlekyqElLtkYTcy")],
        [InlineKeyboardButton(text="я уже подписан", callback_data="subscribed")]
    ])