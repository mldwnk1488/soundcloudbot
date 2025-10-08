from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from services.queue_manager import queue_manager
from lang_bot.translations import get_text

router = Router()

@router.message(Command("queue"))
async def queue_handler(message: Message):
    """Показываю текущую позицию в очереди"""
    user_id = message.from_user.id
    lang = getattr(message, 'user_language', 'ua')
    
    if user_id in queue_manager.queue_status:
        pos = queue_manager.get_queue_position(user_id)
        if pos > 0:
            await message.answer(
                f"📊 {get_text(lang, 'your_queue_number')}: {pos}\n"
                f"{get_text(lang, 'total_in_queue')}: {len(queue_manager.download_queue)}"
            )
        else:
            await message.answer(get_text(lang, "processing_now"))
    else:
        await message.answer(get_text(lang, "not_in_queue"))