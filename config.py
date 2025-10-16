# config.py
import os
import logging

def load_env_file():
    """Загружает переменные из .env файла если существует"""
    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            print(f"🔍 Найден .env файл")
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key not in os.environ:
                            os.environ[key] = value
                            print(f"✅ Загружено из .env: {key}")
        else:
            print("🔍 .env файл не найден, используем переменные окружения")
    except Exception as e:
        print(f"⚠️ Ошибка чтения .env файла: {e}")

# 🔥 ДЛЯ ДЕПЛОЯ: загружаем .env только локально
if not os.environ.get("RENDER") and not os.environ.get("KOYEB") and not os.environ.get("HEROKU"):
    load_env_file()

# 🔥 ОПРЕДЕЛЯЕМ ХОСТИНГ
RENDER = "RENDER" in os.environ
KOYEB = "KOYEB" in os.environ  
HEROKU = "HEROKU" in os.environ
PYTHONANYWHERE = "PYTHONANYWHERE" in os.environ
LOCAL = not RENDER and not KOYEB and not HEROKU and not PYTHONANYWHERE

# 🔥 ОСНОВНЫЕ НАСТРОЙКИ
DEBUG = os.environ.get("DEBUG", "false").lower() == "true" and LOCAL
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# 🔥 ПРОВЕРКА ТОКЕНА
if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
    if RENDER:
        print("💡 На Render установите переменную окружения BOT_TOKEN")
    elif KOYEB:
        print("💡 На Koyeb установите переменную окружения BOT_TOKEN")
    elif HEROKU:
        print("💡 На Heroku установите переменную окружения BOT_TOKEN")
    elif PYTHONANYWHERE:
        print("💡 На PythonAnywhere установите переменную окружения BOT_TOKEN")
    else:
        print("💡 Создайте файл .env с содержимым: BOT_TOKEN=your_token")
    exit(1)

# 🔥 ОПТИМИЗИРОВАННЫЕ НАСТРОЙКИ ДЛЯ КАЖДОГО ХОСТИНГА
if KOYEB:
    # 🔥 НАСТРОЙКИ ДЛЯ KOYEB - БОЛЬШЕ РЕСУРСОВ
    MAX_TRACKS_PER_USER = 15
    MAX_DOWNLOAD_SIZE_MB = 100
    DOWNLOAD_TIMEOUT = 180
    YOUTUBE_MAX_RETRIES = 5
    ENABLE_PROXY = True
    LOG_LEVEL = "INFO"
    print("🎯 Режим: KOYEB (оптимизированный)")

elif RENDER:
    # 🔥 НАСТРОЙКИ ДЛЯ RENDER - БАЛАНС
    MAX_TRACKS_PER_USER = 10
    MAX_DOWNLOAD_SIZE_MB = 50
    DOWNLOAD_TIMEOUT = 120
    YOUTUBE_MAX_RETRIES = 3
    ENABLE_PROXY = False
    LOG_LEVEL = "INFO"
    print("🎯 Режим: RENDER (сбалансированный)")

elif HEROKU:
    # 🔥 НАСТРОЙКИ ДЛЯ HEROKU - МИНИМАЛЬНЫЕ
    MAX_TRACKS_PER_USER = 5
    MAX_DOWNLOAD_SIZE_MB = 25
    DOWNLOAD_TIMEOUT = 90
    YOUTUBE_MAX_RETRIES = 2
    ENABLE_PROXY = False
    LOG_LEVEL = "INFO"
    print("🎯 Режим: HEROKU (экономный)")

elif PYTHONANYWHERE:
    # 🔥 НАСТРОЙКИ ДЛЯ PYTHONANYWHERE - ОГРАНИЧЕННЫЕ
    MAX_TRACKS_PER_USER = 8
    MAX_DOWNLOAD_SIZE_MB = 40
    DOWNLOAD_TIMEOUT = 150
    YOUTUBE_MAX_RETRIES = 3
    ENABLE_PROXY = True
    LOG_LEVEL = "INFO"
    print("🎯 Режим: PYTHONANYWHERE (ограниченный)")

else:
    # 🔥 НАСТРОЙКИ ДЛЯ ЛОКАЛЬНОЙ РАЗРАБОТКИ
    MAX_DOWNLOAD_SIZE_MB = int(os.environ.get("MAX_DOWNLOAD_SIZE_MB", "500"))
    MAX_TRACKS_PER_USER = int(os.environ.get("MAX_TRACKS_PER_USER", "50"))
    DOWNLOAD_TIMEOUT = int(os.environ.get("DOWNLOAD_TIMEOUT", "600"))
    YOUTUBE_MAX_RETRIES = int(os.environ.get("YOUTUBE_MAX_RETRIES", "10"))
    YOUTUBE_TIMEOUT = int(os.environ.get("YOUTUBE_TIMEOUT", "60"))
    ENABLE_PROXY = os.environ.get("ENABLE_PROXY", "false").lower() == "true"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
    print("🎯 Режим: LOCAL (полные возможности)")

# 🔥 ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7021944306"))
ENABLE_YOUTUBE_DEBUG = False
SAVE_DOWNLOADED_FILES = False

# 🔥 ПРОКСИ СЕРВЕРА (используются только если ENABLE_PROXY = True)
PROXY_LIST = [
    'http://45.155.68.129:8133',
    'http://45.94.47.66:8110', 
    'http://154.95.36.199:6893',
    'https://185.199.229.156:7492',
    'https://185.199.228.220:7300',
    None  # Прямое соединение как запасной вариант
]

# 🔥 РЕКЛАМНОЕ СООБЩЕНИЕ
AD_MESSAGE = {
    "ua": "📢 *Підпишись на мій канал!*",
    "ru": "📢 *Подпишись на мой канал!*", 
    "en": "📢 *Subscribe to my channel!*"
}

# 🔥 НАСТРОЙКА ЛОГИРОВАНИЯ
def setup_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=log_format,
        handlers=[logging.StreamHandler()]
    )
    
    # ВЫКЛЮЧАЕМ ШУМНЫЕ ЛОГИ НА ПРОДАКШЕНЕ
    if not DEBUG:
        logging.getLogger('yt-dlp').setLevel(logging.ERROR)
        logging.getLogger('aiohttp').setLevel(logging.WARNING)
        logging.getLogger('aiogram').setLevel(logging.INFO)

# 🔥 ИНФОРМАЦИЯ ПРИ СТАРТЕ
def print_startup_info():
    print("=" * 50)
    print("🚀 SOUNDCLOUD MUSIC BOT")
    print("=" * 50)
    
    if KOYEB:
        print("📍 Хостинг: KOYEB 🆕")
    elif RENDER:
        print("📍 Хостинг: RENDER")
    elif HEROKU:
        print("📍 Хостинг: HEROKU")
    elif PYTHONANYWHERE:
        print("📍 Хостинг: PYTHONANYWHERE")
    else:
        print("📍 Хостинг: LOCAL 🖥️")
        
    print(f"🌐 Прокси: {'ENABLED' if ENABLE_PROXY else 'DISABLED'}")
    print(f"🎵 Макс. треков: {MAX_TRACKS_PER_USER}")
    print(f"💾 Макс. размер: {MAX_DOWNLOAD_SIZE_MB}MB")
    print(f"🔄 Попытки: {YOUTUBE_MAX_RETRIES}")
    print(f"⏱ Таймаут: {DOWNLOAD_TIMEOUT}сек")
    print(f"📊 Логи: {LOG_LEVEL}")
    print(f"🤖 Бот: ACTIVE ✅")
    print("=" * 50)

# АВТОМАТИЧЕСКАЯ ИНИЦИАЛИЗАЦИЯ
setup_logging()
print_startup_info()