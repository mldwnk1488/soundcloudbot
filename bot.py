import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
import os
import aiohttp
from datetime import datetime

from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.queue import router as queue_router
from handlers.download import router as download_router

# HTTP-заглушка
async def health_check(request):
    print(f"Health check at {datetime.now()}")
    return web.Response(text='Bot Health OK')

# Самопинг
async def self_ping():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                # Замени на свой реальный URL
                async with session.get('https://your-bot-name.onrender.com/') as resp:
                    print(f"Self-ping: {resp.status} at {datetime.now()}")
        except Exception as e:
            print(f"Ping failed: {e}")
        await asyncio.sleep(300)  # Каждые 5 минут

async def start_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(queue_router)
    dp.include_router(download_router)
    await dp.start_polling(bot)

async def start_http():
    app = web.Application()
    app.router.add_get('/', health_check)
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"HTTP server started on port {port}")
    # Бесконечно ждем
    await asyncio.Future()

async def main():
    # Запускаем самопинг в фоне
    asyncio.create_task(self_ping())
    
    # Запускаем оба сервиса параллельно
    await asyncio.gather(
        start_http(),
        start_bot()
    )

if __name__ == "__main__":
    asyncio.run(main())
