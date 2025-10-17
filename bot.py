import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError, TelegramUnauthorizedError
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_health_server(port=10000):
    """Health check сервер для Render"""
    try:
        from aiohttp import web
        
        app = web.Application()
        
        async def health_check(request):
            return web.json_response({"status": "healthy", "service": "music-bot"})
        
        app.router.add_get('/health', health_check)
        app.router.add_get('/', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"🌐 Health server started on port {port}")
        return runner
    except ImportError:
        logger.warning("⚠️ aiohttp не установлен, health server отключен")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка health server: {e}")
        return None

async def main():
    # Проверка токена
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден!")
        return
    
    try:
        # Создаем бота
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Проверяем авторизацию
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот авторизован: @{bot_info.username}")
        
        # Настройка диспетчера
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Импортируем роутеры
        try:
            from handlers.start import router as start_router
            from handlers.search import router as search_router
            from handlers.download import router as download_router
            from handlers.queue import router as queue_router
            from handlers.admin import router as admin_router
            
            dp.include_router(start_router)
            dp.include_router(search_router)
            dp.include_router(download_router)
            dp.include_router(queue_router)
            dp.include_router(admin_router)
            
            logger.info("✅ Все роутеры подключены")
        except ImportError as e:
            logger.warning(f"⚠️ Некоторые роутеры не найдены: {e}")
        
        # Запускаем health server
        health_runner = await start_health_server()
        
        # Запускаем бота
        logger.info("🎵 Бот готов к работе!")
        await dp.start_polling(bot)
        
    except TelegramUnauthorizedError:
        logger.error("❌ Неверный BOT_TOKEN! Проверь токен в @BotFather")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
    finally:
        # Корректное завершение
        if 'health_runner' in locals() and health_runner:
            await health_runner.cleanup()
        if 'bot' in locals():
            await bot.session.close()
        logger.info("👋 Завершение работы бота")

if __name__ == "__main__":
    asyncio.run(main())
