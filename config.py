import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")

# Рекламное сообщение
AD_MESSAGE = """
от души что бота юзаешь

⬇️⬇️⬇️
"""