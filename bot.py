import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
import os
import logging

from config import BOT_TOKEN, KOYEB
from database import db
from core import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = None
routers_configured = False

async def health_check(request):
    return web.Response(text='Bot is running on Koyeb!')

async def start_http_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.environ.get("PORT", 8000))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"HTTP server started on port {port}")
    return runner

def setup_routers():
    global dp, routers_configured
    
    if routers_configured:
        logger.info("Роутеры уже настроены")
        return dp
        
    if dp is None:
        dp = Dispatcher()
    
    from handlers.start import router as start_router
    from handlers.download import router as download_router
    from handlers.admin import router as admin_router
    from handlers.queue import router as queue_router
    from handlers.search import router as search_router  # ДОБАВЛЕНО
    
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(queue_router)
    dp.include_router(download_router)
    dp.include_router(search_router)  # ДОБАВЛЕНО
    
    routers_configured = True
    logger.info("Все роутеры подключены")
    return dp

async def start_bot():
    bot = Bot(token=BOT_TOKEN)
    
    logger.info("Инициализация для Koyeb...")
    
    db_manager.set_db(db)
    
    dp = setup_routers()
    
    http_runner = await start_http_server()
    
    logger.info("Бот запускается...")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка бота: {e}")
        raise
    finally:
        await http_runner.cleanup()

async def main():
    try:
        await db.init_db()
        logger.info("База данных готова")
        
        await start_bot()
        
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")