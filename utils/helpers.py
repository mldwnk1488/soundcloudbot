from aiogram import Bot
from aiogram.types import FSInputFile

from config import AD_MESSAGE
from keyboards.main import get_ad_keyboard

async def send_message_to_user(bot: Bot, user_id: int, text: str):


    """Отправляю сообщение юзеру"""
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        print(f"❌не удалось отправить сообщение юзеру {user_id}: {e}")

async def send_document_to_user(bot: Bot, user_id: int, document, caption: str = ""):


    """Отправляю документ юзеру"""
    try:
        await bot.send_document(user_id, document, caption=caption)
    except Exception as e:
        print(f"❌не удалось отправить документ юзеру {user_id}: {e}")

async def send_ad_message(bot: Bot, user_id: int):


    """Отправляю рекламное сообщение"""
    try:
        await bot.send_message(
            user_id,
            AD_MESSAGE,
            reply_markup=get_ad_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌не удалось отправить рекламу юзеру {user_id}: {e}")