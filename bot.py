import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
import os

from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.queue import router as queue_router
from handlers.download import router as download_router

# HTTP-заглушка для Render
async def handle(request):
    return web.Response(text="Bot is running")

async def start_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_router(start_router)
    dp.include_router(queue_router)
    dp.include_router(download_router)
    
    await dp.start_polling(bot)

async def main():
    # Запускаем HTTP-сервер
    app = web.Application()
    app.router.add_get('/', handle)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 3000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"HTTP server started on port {port}")
    
    # Запускаем бота
    await start_bot()

if __name__ == "__main__":
    asyncio.run(main())

