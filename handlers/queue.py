from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from services.queue_manager import queue_manager

router = Router()

@router.message(Command("queue"))
async def queue_handler(message: Message):
    """Показываю текущую позицию в очереди"""
    user_id = message.from_user.id
    
    if user_id in queue_manager.queue_status:
        pos = queue_manager.get_queue_position(user_id)
        if pos > 0:
            await message.answer(f"📊твоя очередь номер: {pos}\nвсего в очереди: {len(queue_manager.download_queue)}")
        else:
            await message.answer("ща все сделаю брат")
    else:
        await message.answer("ты сначала в очередь стань")