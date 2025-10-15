# handlers/start.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.language_kb import get_language_keyboard, get_agreement_keyboard
from keyboards.main import get_ad_keyboard, get_search_keyboard
from lang_bot.translations import get_text
from core import db_manager
from utils import get_user_language_safe

router = Router()

class UserStates(StatesGroup):
    waiting_for_agreement = State()

@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    db = db_manager.get_db()
    
    try:
        user_language = await db.get_user_language(message.from_user.id)
        
        if user_language == 'ua':
            await db.add_user(
                message.from_user.id,
                message.from_user.username,
                message.from_user.first_name,
                message.from_user.last_name,
                'ua'
            )
        
        current_state = await state.get_state()
        if current_state:
            await state.clear()
        
        await message.answer(
            get_text("ua", "start_choose"),
            parse_mode="HTML",
            reply_markup=get_language_keyboard()
        )
        await state.set_state(UserStates.waiting_for_agreement)
        
    except Exception as e:
        print(f"Ошибка в start_handler: {e}")
        await message.answer(
            "🌍 <b>Choose language / Оберіть мову / Выберите язык</b>",
            parse_mode="HTML", 
            reply_markup=get_language_keyboard()
        )
        await state.set_state(UserStates.waiting_for_agreement)

@router.callback_query(F.data.startswith("lang_"), UserStates.waiting_for_agreement)
async def select_language(callback: CallbackQuery, state: FSMContext):
    try:
        lang = callback.data.split("_")[1]
        
        db = db_manager.get_db()
        await db.update_user_language(callback.from_user.id, lang)
        
        await state.update_data(language=lang)
        
        disclaimer_text = get_disclaimer_text(lang)
        await callback.message.edit_text(
            disclaimer_text,
            parse_mode="Markdown",
            reply_markup=get_agreement_keyboard(lang)
        )
        
    except Exception as e:
        print(f"Ошибка в select_language: {e}")
        await callback.answer("❌ Ошибка выбора языка", show_alert=True)

@router.callback_query(F.data.startswith("agree_"), UserStates.waiting_for_agreement)
async def process_agreement(callback: CallbackQuery, state: FSMContext):
    try:
        lang = callback.data.split("_")[1]
        user_id = callback.from_user.id
        
        await state.update_data(user_language=lang)
        
        welcome_text = get_text(lang, "welcome")
        main_text = get_text(lang, "main_text")
        
        keyboard = get_ad_keyboard(lang)
        keyboard.inline_keyboard.append([get_search_keyboard(lang).inline_keyboard[0][0]])
        
        await callback.message.edit_text(
            f"{welcome_text}{main_text}",
            reply_markup=keyboard
        )
        
        await state.clear()
        
    except Exception as e:
        print(f"Ошибка в process_agreement: {e}")
        await callback.answer("❌ Ошибка обработки соглашения", show_alert=True)
    finally:
        current_state = await state.get_state()
        if current_state:
            await state.clear()

@router.callback_query(F.data == "subscribed")
async def callback_subscribed(callback: CallbackQuery):
    try:
        lang = await get_user_language_safe(callback.from_user.id)
        alert_text = get_text(lang, "subscribed_alert")
        await callback.answer(alert_text, show_alert=True)
    except Exception as e:
        print(f"Ошибка в callback_subscribed: {e}")
        await callback.answer("Спасибо!", show_alert=True)

@router.message(Command("test"))
async def test_handler(message: Message):
    print("✅ ТЕСТОВАЯ КОМАНДА СРАБОТАЛА!")
    await message.answer("Тест работает!")

@router.message(Command("help"))
async def help_handler(message: Message):
    try:
        lang = await get_user_language_safe(message.from_user.id)
        help_text = get_text(lang, "main_text")
        await message.answer(help_text)
    except Exception as e:
        print(f"Ошибка в help_handler: {e}")
        await message.answer(get_text("ua", "main_text"))

def get_disclaimer_text(language):
    texts = {
        "ua": "🎵 *УМОВИ ВИКОРИСТАННЯ ТА ДИСКЛЕЙМЕР*\n\n_Я створив цього бота з душею — забезпечити доступ до музики в умовах відсутності інтернету_\n\n💙 *МОЯ МIСIЯ*\nНадати можливість кожній людині створити особистий музичний резерв для підтримки психологічного стану під час перебоїв з електропостачанням.",
        "ru": "🎵 *УСЛОВИЯ ИСПОЛЬЗОВАНИЯ И ДИСКЛЕЙМЕР*\n\n_Я сделал этого бота с душой — обеспечить доступ к музыке в условиях отсутствия интернета_\n\n💙 *МОЯ МИССИЯ*\nДать возможность каждому человеку создать личный музыкальный резерв для поддержания психологического состояния во время перебоев с электропитанием.",
        "en": "🎵 *TERMS OF USE AND DISCLAIMER*\n\n_I made this bot with soul — to provide access to music during internet outages_\n\n💙 *MY MISSION*\nTo give every person the opportunity to create a personal music reserve to maintain psychological well-being during power outages."
    }
    return texts.get(language, texts["ua"])

Теперь обновлю config.py - уберу YouTube настройки:
python

import os
import logging

def load_env_file():
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

if not os.environ.get("RENDER") and not os.environ.get("KOYEB"):
    load_env_file()

RENDER = "RENDER" in os.environ
KOYEB = "KOYEB" in os.environ  
LOCAL = not RENDER and not KOYEB

DEBUG = os.environ.get("DEBUG", "false").lower() == "true" and not RENDER and not KOYEB
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
    if RENDER:
        print("💡 На Render установите переменную окружения BOT_TOKEN")
    elif KOYEB:
        print("💡 На Koyeb установите переменную окружения BOT_TOKEN")
    else:
        print("💡 Создайте файл .env с содержимым: BOT_TOKEN=your_token")
    exit(1)

if KOYEB:
    MAX_TRACKS_PER_USER = 12
    MAX_DOWNLOAD_SIZE_MB = 80
    DOWNLOAD_TIMEOUT = 180
    ENABLE_PROXY = False
    LOG_LEVEL = "INFO"
    print("🎯 Режим: KOYEB")

elif RENDER:
    MAX_TRACKS_PER_USER = 5
    MAX_DOWNLOAD_SIZE_MB = 25
    DOWNLOAD_TIMEOUT = 90
    ENABLE_PROXY = False
    LOG_LEVEL = "INFO"
    print("🎯 Режим: RENDER")

else:
    MAX_DOWNLOAD_SIZE_MB = int(os.environ.get("MAX_DOWNLOAD_SIZE_MB", "100"))
    MAX_TRACKS_PER_USER = int(os.environ.get("MAX_TRACKS_PER_USER", "20"))
    DOWNLOAD_TIMEOUT = int(os.environ.get("DOWNLOAD_TIMEOUT", "300"))
    ENABLE_PROXY = False
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
    print("🎯 Режим: LOCAL")

ADMIN_ID = int(os.environ.get("ADMIN_ID", "7021944306"))
ENABLE_YOUTUBE_DEBUG = False
SAVE_DOWNLOADED_FILES = False

AD_MESSAGE = {
    "ua": "📢 *Підпишись на мій канал!*",
    "ru": "📢 *Подпишись на мой канал!*", 
    "en": "📢 *Subscribe to my channel!*"
}

def setup_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=log_format,
        handlers=[logging.StreamHandler()]
    )
    
    logging.getLogger('yt-dlp').setLevel(logging.ERROR)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

def print_startup_info():
    print("=" * 50)
    print("🚀 MUSIC BOT")
    print("=" * 50)
    
    if KOYEB:
        print("📍 Хостинг: KOYEB 🆕")
    elif RENDER:
        print("📍 Хостинг: RENDER")
    else:
        print("📍 Хостинг: LOCAL")
        
    print(f"🎵 Макс. треков: {MAX_TRACKS_PER_USER}")
    print(f"💾 Макс. размер: {MAX_DOWNLOAD_SIZE_MB}MB")
    print(f"⏱ Таймаут загрузки: {DOWNLOAD_TIMEOUT}сек")
    print(f"🤖 Бот: ACTIVE ✅")
    print("=" * 50)

setup_logging()
print_startup_info()