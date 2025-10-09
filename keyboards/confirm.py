from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from lang_bot.translations import get_text

def get_confirm_keyboard(language="ua"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=get_text(language, "yes_download"), 
                callback_data="confirm_redownload"
            ),
            InlineKeyboardButton(
                text=get_text(language, "no_cancel"), 
                callback_data="cancel_redownload"
            )
        ]
    ])