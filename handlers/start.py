from aiogram import Router, F
from aiogram.types import Message, CallbackQuery  # ← Убедись что это есть
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.language_kb import get_language_keyboard, get_agreement_keyboard
from keyboards.main import get_ad_keyboard, get_search_keyboard
from lang_bot.translations import get_text
from core import db_manager
from utils import get_user_language_safe
import logging

logger = logging.getLogger(__name__)

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
        logger.error(f"Ошибка в start_handler: {e}")
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
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в select_language: {e}")
        try:
            await callback.answer("❌ Ошибка выбора языка", show_alert=True)
        except:
            pass

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
        
        await callback.answer()
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка в process_agreement: {e}")
        try:
            await callback.answer("❌ Ошибка обработки соглашения", show_alert=True)
        except:
            pass
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
        logger.error(f"Ошибка в callback_subscribed: {e}")
        try:
            # Если не удалось ответить с алертом, пробуем просто ответить
            await callback.answer()
        except:
            # Если и это не удалось, игнорируем ошибку
            pass

@router.message(Command("test"))
async def test_handler(message: Message):
    logger.info("✅ ТЕСТОВАЯ КОМАНДА СРАБОТАЛА!")
    await message.answer("Тест работает!")

@router.message(Command("help"))
async def help_handler(message: Message):
    try:
        lang = await get_user_language_safe(message.from_user.id)
        help_text = get_text(lang, "main_text")
        await message.answer(help_text)
    except Exception as e:
        logger.error(f"Ошибка в help_handler: {e}")
        await message.answer(get_text("ua", "main_text"))

def get_disclaimer_text(language):
    texts = {
        "ua": "🎵 *УМОВИ ВИКОРИСТАННЯ ТА ДИСКЛЕЙМЕР*\n\n_Я створив цього бота з душею — забезпечити доступ до музики в умовах відсутності інтернету_\n\n💙 *МОЯ МIСIЯ*\nНадати можливість кожній людині створити особистий музичний резерв для підтримки психологічного стану під час перебоїв з електропостачанням.",
        "ru": "🎵 *УСЛОВИЯ ИСПОЛЬЗОВАНИЯ И ДИСКЛЕЙМЕР*\n\n_Я сделал этого бота с душой — обеспечить доступ к музыке в условиях отсутствия интернета_\n\n💙 *МОЯ МИССИЯ*\nДать возможность каждому человеку создать личный музыкальный резерв для поддержания психологического состояния во время перебоев с электропитанием.",
        "en": "🎵 *TERMS OF USE AND DISCLAIMER*\n\n_I made this bot with soul — to provide access to music during internet outages_\n\n💙 *MY MISSION*\nTo give every person the opportunity to create a personal music reserve to maintain psychological well-being during power outages."
    }
    return texts.get(language, texts["ua"])