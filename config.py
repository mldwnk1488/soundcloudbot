import os

# 🔥 УБРАЛ DOTENV - ИСПОЛЬЗУЕМ ТОЛЬКО OS
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

# Рекламное сообщение
AD_MESSAGE = {
    "ua": "📢 *Підпишись на мій канал!*\nМоже щось буду туди постити...",
    "ru": "📢 *Подпишись на мой канал!*\nМожет буду туда что-то постить...", 
    "en": "📢 *Subscribe to my channel!*\nMaybe I'll post something there..."
}
