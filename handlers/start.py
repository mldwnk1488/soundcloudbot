from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.language_kb import get_language_keyboard, get_agreement_keyboard
from keyboards.main import get_ad_keyboard
from lang_bot.translations import get_text, TRANSLATIONS
from bot_data import get_db  # <-- ДОБАВИЛ

router = Router()

class UserStates(StatesGroup):
    waiting_for_agreement = State()

@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    db = get_db()  # <-- ИСПРАВИЛ
    
    user_language = await db.get_user_language(message.from_user.id)
    
    if user_language == 'ua':
        await db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name,
            'ua'
        )
    
    await message.answer(
        get_text("ua", "start_choose"),
        parse_mode="HTML",
        reply_markup=get_language_keyboard()
    )
    await state.set_state(UserStates.waiting_for_agreement)

@router.callback_query(F.data.startswith("lang_"), UserStates.waiting_for_agreement)
async def select_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    
    db = get_db()  # <-- ИСПРАВИЛ
    await db.update_user_language(callback.from_user.id, lang)
    
    await state.update_data(language=lang)
    
    disclaimer_text = get_disclaimer_text(lang)
    await callback.message.edit_text(
        disclaimer_text,
        parse_mode="Markdown",
        reply_markup=get_agreement_keyboard(lang)
    )

@router.callback_query(F.data.startswith("agree_"), UserStates.waiting_for_agreement)
async def process_agreement(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    from services.queue_manager import queue_manager
    queue_manager.user_languages[user_id] = lang
    
    await state.update_data(user_language=lang)
    await state.clear()
    
    welcome_text = get_text(lang, "welcome")
    main_text = get_text(lang, "main_text")
    
    await callback.message.edit_text(
        f"{welcome_text}{main_text}",
        reply_markup=get_ad_keyboard(lang)
    )
    await callback.answer()

@router.callback_query(F.data == "subscribed")
async def callback_subscribed(callback: CallbackQuery):
    db = get_db()  # <-- ИСПРАВИЛ
    lang = await db.get_user_language(callback.from_user.id)
    
    alert_text = get_text(lang, "subscribed_alert")
    await callback.answer(alert_text, show_alert=True)

def get_disclaimer_text(language):
    texts = {
        "ua": """🎵 *УМОВИ ВИКОРИСТАННЯ ТА ДИСКЛЕЙМЕР*\n\n_Я створив цього бота з душею — забезпечити доступ до музики в умовах відсутності інтернету_\n\n💙 *МОЯ МIСIЯ*\nНадати можливість кожній людині створити особистий музичний резерв для підтримки психологічного стану під час перебоїв з електропостачанням.\n\n✅ *ДОЗВОЛЕНО*\n• Використовувати музику ВИКЛЮЧНО для особистого некомерційного прослуховування\n• Зберігати треки на своїх пристроях для офлайн-доступу\n• Створювати резервні копії улюблених плейлистів "на чорний день"\n• Ділитися музикою в особистому спілкуванні з близькими\n\n🚫 *СУВОРО ЗАБОРОНЕНО*\n• Розповсюджувати музику через інші платформи та сайти\n• Використовувати для комерційних цілей та монетизації\n• Порушувати авторські права виконавців\n• Видавати завантажену музику за власну творчість\n\n🎯 *ЯК КОРИСТУВАТИСЯ ЕФЕКТИВНО*\n1. У спокійний час створіть плейлист "екстрений резерв"\n2. Завантажте його через бота та збережіть на телефон\n3. Додайте також на флеш-носій як додаткову копію\n\n🛡️ *ПОВАГА ДО АРТИСТІВ*\nПам'ятайте — музика це чиясь творчість. Якщо трек вам допомагає:\n• Знайдіть артиста на SoundCloud та підпишіться\n• Залишайте лайки та коментарі на оригінальних треках\n• Діліться посиланнями на творчість виконавця\n• Якщо з'явиться можливість — фінансово підтримайте\n\n⚠️ *ВАЖЛИВО*\nВикористовуючи цього бота, ви автоматично погоджуєтесь:\n• Нести повну відповідальність за дотримання авторських прав\n• Використовувати музику виключно в особистих цілях\n• Не розповсюджувати завантажені матеріали""",
        "ru": """🎵 *УСЛОВИЯ ИСПОЛЬЗОВАНИЯ И ДИСКЛЕЙМЕР*\n\n_Я сделал этого бота с душой — обеспечить доступ к музыке в условиях отсутствия интернета_\n\n💙 *МОЯ МИССИЯ*\nДать возможность каждому человеку создать личный музыкальный резерв для поддержания психологического состояния во время перебоев с электропитанием.\n\n✅ *РАЗРЕШЕНО*\n• Использовать музыку ИСКЛЮЧИТЕЛЬНО для личного некоммерческого прослушивания\n• Сохранять треки на своих устройствах для офлайн-доступа\n• Создавать резервные копии любимых плейлистов "на черный день"\n• Делиться музыкой в личном общении с близкими\n\n🚫 *СТРОГО ЗАПРЕЩЕНО*\n• Распространять музыку через другие платформы и сайты\n• Использовать для комерческих целей и монетизации\n• Нарушать авторские права исполнителей\n• Выдавать загруженную музыку за собственное творчество\n\n🎯 *КАК ПОЛЬЗОВАТЬСЯ ЭФФЕКТИВНО*\n1. В спокойное время создайте плейлист "экстренный резерв"\n2. Загрузите его через бота и сохраните на телефон\n3. Добавьте также на флеш-носитель как дополнительную копию\n\n🛡️ *УВАЖЕНИЕ К АРТИСТАМ*\nПомните — музыка это чье-то творчество. Если трек вам помогает:\n• Найдите артиста на SoundCloud и подпишитесь\n• Оставляйте лайки и комментарии на оригинальных треках\n• Делитесь ссылками на творчество исполнителя\n• Если появится возможность — финансово поддержите\n\n⚠️ *ВАЖНО*\nИспользуя этого бота, вы автоматически соглашаетесь:\n• Нести полную ответственность за соблюдение авторских прав\n• Использовать музыку исключительно в личных целях\n• Не распространять загруженные материалы""", 
        "en": """🎵 *TERMS OF USE AND DISCLAIMER*\n\n_I made this bot with soul — to provide access to music during internet outages_\n\n💙 *MY MISSION*\nTo give every person the opportunity to create a personal music reserve to maintain psychological well-being during power outages.\n\n✅ *ALLOWED*\n• Use music EXCLUSIVELY for personal non-commercial listening\n• Save tracks on your devices for offline access\n• Create backup copies of favorite playlists "for a rainy day"\n• Share music in personal communication with close ones\n\n🚫 *STRICTLY PROHIBITED*\n• Distribute music through other platforms and websites\n• Use for commercial purposes and monetization\n• Violate artists' copyrights\n• Present downloaded music as your own creation\n\n🎯 *HOW TO USE EFFECTIVELY*\n1. During calm times, create an "emergency reserve" playlist\n2. Download it through the bot and save it on your phone\n3. Also add it to a flash drive as an additional copy\n\n🛡️ *RESPECT FOR ARTISTS*\nRemember — music is someone's creativity. If a track helps you:\n• Find the artist on SoundCloud and subscribe\n• Leave likes and comments on original tracks\n• Share links to the performer's work\n• If possible — provide financial support\n\n⚠️ *IMPORTANT*\nBy using this bot, you automatically agree:\n• To take full responsibility for copyright compliance\n• To use music exclusively for personal purposes\n• Not to distribute downloaded materials"""
    }
    return texts.get(language, texts["ua"])

@router.message(Command("test"))
async def test_handler(message: Message):
    print("✅ ТЕСТОВАЯ КОМАНДА СРАБОТАЛА!")
    await message.answer("Тест работает!")