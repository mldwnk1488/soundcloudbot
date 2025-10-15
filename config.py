import os
import logging

# 🔥 ПРОСТАЯ ЗАГРУЗКА .env БЕЗ БИБЛИОТЕКИ
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
                        # Устанавливаем только если еще не установлено
                        if key not in os.environ:
                            os.environ[key] = value
                            print(f"✅ Загружено из .env: {key}")
        else:
            print("🔍 .env файл не найден, используем переменные окружения")
    except Exception as e:
        print(f"⚠️ Ошибка чтения .env файла: {e}")

# 🔥 ЗАГРУЖАЕМ .env ТОЛЬКО ЛОКАЛЬНО
if not os.environ.get("RENDER") and not os.environ.get("KOYEB"):
    load_env_file()

# 🔥 ОПРЕДЕЛЯЕМ ХОСТИНГ
RENDER = "RENDER" in os.environ
KOYEB = "KOYEB" in os.environ  
LOCAL = not RENDER and not KOYEB

DEBUG = os.environ.get("DEBUG", "false").lower() == "true" and not RENDER and not KOYEB
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# 🔥 ПРОВЕРКА ТОКЕНА
if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
    if RENDER:
        print("💡 На Render установите переменную окружения BOT_TOKEN")
    elif KOYEB:
        print("💡 На Koyeb установите переменную окружения BOT_TOKEN")
    else:
        print("💡 Создайте файл .env с содержимым: BOT_TOKEN=your_token")
    exit(1)

# 🔥 ОПТИМИЗИРОВАННЫЕ НАСТРОЙКИ ДЛЯ КАЖДОГО ХОСТИНГА
if KOYEB:
    # 🔥 НАСТРОЙКИ ДЛЯ KOYEB - БОЛЬШЕ РЕСУРСОВ
    MAX_TRACKS_PER_USER = 12
    MAX_DOWNLOAD_SIZE_MB = 80
    DOWNLOAD_TIMEOUT = 180
    YOUTUBE_MAX_RETRIES = 5
    ENABLE_PROXY = True
    LOG_LEVEL = "INFO"
    print("🎯 Режим: KOYEB (оптимизированный)")

elif RENDER:
    # 🔥 НАСТРОЙКИ ДЛЯ RENDER - МИНИМАЛЬНЫЕ
    MAX_TRACKS_PER_USER = 5
    MAX_DOWNLOAD_SIZE_MB = 25
    DOWNLOAD_TIMEOUT = 90
    YOUTUBE_MAX_RETRIES = 2
    ENABLE_PROXY = False
    LOG_LEVEL = "INFO"
    print("🎯 Режим: RENDER (экономный)")

else:
    # 🔥 НАСТРОЙКИ ДЛЯ ЛОКАЛЬНОЙ РАЗРАБОТКИ
    MAX_DOWNLOAD_SIZE_MB = int(os.environ.get("MAX_DOWNLOAD_SIZE_MB", "100"))
    MAX_TRACKS_PER_USER = int(os.environ.get("MAX_TRACKS_PER_USER", "20"))
    DOWNLOAD_TIMEOUT = int(os.environ.get("DOWNLOAD_TIMEOUT", "300"))
    YOUTUBE_MAX_RETRIES = int(os.environ.get("YOUTUBE_MAX_RETRIES", "8"))
    YOUTUBE_TIMEOUT = int(os.environ.get("YOUTUBE_TIMEOUT", "30"))
    ENABLE_PROXY = os.environ.get("ENABLE_PROXY", "true").lower() == "true"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
    print("🎯 Режим: LOCAL (полные возможности)")

# 🔥 ПРОКСИ СЕРВЕРА (используются только если ENABLE_PROXY = True)
PROXY_LIST = [
    'http://45.155.68.129:8133',
    'http://45.94.47.66:8110', 
    'http://154.95.36.199:6893',
    'https://185.199.229.156:7492',
    'https://185.199.228.220:7300',
    None  # Прямое соединение как запасной вариант
]

# 🔥 ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7021944306"))
ENABLE_YOUTUBE_DEBUG = False
SAVE_DOWNLOADED_FILES = False

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
    
    # ВЫКЛЮЧАЕМ ШУМНЫЕ ЛОГИ
    logging.getLogger('yt-dlp').setLevel(logging.ERROR)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

# 🔥 ИНФОРМАЦИЯ ПРИ СТАРТЕ
def print_startup_info():
    print("=" * 50)
    print("🚀 YOUTUBE MUSIC BOT")
    print("=" * 50)
    
    if KOYEB:
        print("📍 Хостинг: KOYEB 🆕")
    elif RENDER:
        print("📍 Хостинг: RENDER")
    else:
        print("📍 Хостинг: LOCAL")
        
    print(f"🌐 Прокси: {'ENABLED' if ENABLE_PROXY else 'DISABLED'}")
    print(f"🎵 Макс. треков: {MAX_TRACKS_PER_USER}")
    print(f"💾 Макс. размер: {MAX_DOWNLOAD_SIZE_MB}MB")
    print(f"🔄 Попытки YouTube: {YOUTUBE_MAX_RETRIES}")
    print(f"⏱ Таймаут загрузки: {DOWNLOAD_TIMEOUT}сек")
    print(f"🤖 Бот: ACTIVE ✅")
    print("=" * 50)

# АВТОМАТИЧЕСКАЯ ИНИЦИАЛИЗАЦИЯ
setup_logging()
print_startup_info()
