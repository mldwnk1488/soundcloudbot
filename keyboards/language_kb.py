from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from lang_bot.translations import get_text

def get_language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_ua"),
            InlineKeyboardButton(text="Русский", callback_data="lang_ru")
        ],
        [
            InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")
        ]
    ])

def get_agreement_keyboard(language="ua"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(language, "agree_button"), callback_data=f"agree_{language}")]
    ])