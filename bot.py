import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.queue import router as queue_router
from handlers.download import router as download_router

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_router(start_router)
    dp.include_router(queue_router)
    dp.include_router(download_router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

