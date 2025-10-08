from aiogram import Bot
from aiogram.types import FSInputFile

from config import AD_MESSAGE
from keyboards.main import get_ad_keyboard
from lang_bot.translations import get_text

async def send_message_to_user(bot: Bot, user_id: int, text: str):
    """Отправляю сообщение юзеру"""
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        print(f"❌ {get_text('ua', 'failed_send_message')} {user_id}: {e}")

async def send_document_to_user(bot: Bot, user_id: int, document, caption: str = ""):
    """Отправляю документ юзеру"""
    try:
        await bot.send_document(user_id, document, caption=caption)
    except Exception as e:
        print(f"❌ {get_text('ua', 'failed_send_document')} {user_id}: {e}")

async def send_ad_message(bot: Bot, user_id: int, lang: str = "ua"):
    """Отправляю рекламное сообщение"""
    try:
        await bot.send_message(
            user_id,
            AD_MESSAGE.get(lang, AD_MESSAGE["ua"]),
            reply_markup=get_ad_keyboard(lang),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌ {get_text('ua', 'failed_send_ad')} {user_id}: {e}")