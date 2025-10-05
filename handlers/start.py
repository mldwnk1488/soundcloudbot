from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from keyboards.main import get_ad_keyboard

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "здарова! это второй подчиненный кости\n\n"
        "1. скинь ссылку на плейлист.\n"
        "2. плейлист должен быть создан человеком.\n"
        "3. какое максимальное колличество треков хз нужно чекать.\n"
        "4. потом выбери удобный формат как тебе отправить их.\n"
        "5. соблюдай очередь чувак\n\n"
        "если будут какие-то ошибки пиши сюда: @kostyalovedota"
    )

@router.callback_query(F.data == "subscribed")
async def callback_subscribed(callback: CallbackQuery):
    await callback.answer("от души брат", show_alert=True)
    