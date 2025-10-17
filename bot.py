import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramConflictError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден!")
        return
    
    logger.info(f"🔑 Токен получен, длина: {len(BOT_TOKEN)} символов")
    
    try:
        # Создаем бота
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Проверяем авторизацию
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот авторизован: @{bot_info.username} (ID: {bot_info.id})")
        
        # Настройка диспетчера
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Подключаем роутеры
        try:
            from handlers.start import router as start_router
            dp.include_router(start_router)
            logger.info("✅ Роутер start подключен")
        except ImportError as e:
            logger.warning(f"⚠️ Роутер start не найден: {e}")
        
        try:
            from handlers.search import router as search_router
            dp.include_router(search_router)
            logger.info("✅ Роутер search подключен")
        except ImportError as e:
            logger.warning(f"⚠️ Роутер search не найден: {e}")
        
        try:
            from handlers.download import router as download_router
            dp.include_router(download_router)
            logger.info("✅ Роутер download подключен")
        except ImportError as e:
            logger.warning(f"⚠️ Роутер download не найден: {e}")
        
        try:
            from handlers.queue import router as queue_router
            dp.include_router(queue_router)
            logger.info("✅ Роутер queue подключен")
        except ImportError as e:
            logger.warning(f"⚠️ Роутер queue не найден: {e}")
        
        try:
            from handlers.admin import router as admin_router
            dp.include_router(admin_router)
            logger.info("✅ Роутер admin подключен")
        except ImportError as e:
            logger.warning(f"⚠️ Роутер admin не найден: {e}")
        
        # 🔥 ЗАПУСКАЕМ ПОЛЛИНГ С ОБРАБОТКОЙ КОНФЛИКТОВ
        logger.info("🚀 Запускаю поллинг...")
        
        # Останавливаем любые предыдущие сессии
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🧹 Вебхук удален, pending updates очищены")
        
        # Запускаем поллинг
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except TelegramConflictError as e:
        logger.error("💥 КОНФЛИКТ: Запущено несколько экземпляров бота!")
        logger.info("💡 Решение: Останови все другие экземпляры бота")
        logger.info("💡 На Render: Restart service или Clear Build Cache")
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
    
    finally:
        if 'bot' in locals():
            await bot.session.close()
        logger.info("👋 Завершение работы")

if __name__ == "__main__":
    print("=" * 50)
    print("🎵 SOUNDCLOUD MUSIC BOT")
    print("=" * 50)
    print("🔍 Запуск бота...")
    
    asyncio.run(main())
