from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from bot_data import get_db
from utils.helpers import send_message_to_user

router = Router()

ADMIN_ID = 7021944306

@router.message(Command("test_admin"))  
async def test_admin_handler(message: Message):
    print("✅ ТЕСТ АДМИНКИ СРАБОТАЛ!")
    await message.answer("Админка работает!")

@router.message(Command("announce"))
async def announce_handler(message: Message):
    print("🔄 ХЕНДЛЕР /announce ВЫЗВАН!")
    user_id = message.from_user.id
    print(f"🆔 Юзер {user_id} пытается использовать /announce")
    
    if user_id != ADMIN_ID:
        print("❌ Не админ")
        await message.answer("❌ Не админ")
        return
    
    announcement_text = message.text.replace('/announce', '').strip()
    
    if not announcement_text:
        await message.answer("❌ Напиши текст: /announce ваш_текст")
        return
    
    print(f"📢 Начинаю рассылку: {announcement_text}")
    
    db = get_db()
    users = await db.get_all_users()
    
    await message.answer(f"📢 Рассылаю {len(users)} юзерам...")
    
    success = 0
    failed = 0
    
    for user_id in users:
        print(f"📨 Отправляю юзеру {user_id}")
        try:
            await send_message_to_user(message.bot, user_id, f"📢 ОБНОВЛЕНИЕ:\n\n{announcement_text}")
            success += 1
            print(f"✅ Отправлено юзеру {user_id}")
        except Exception as e:
            print(f"❌ Не удалось отправить {user_id}: {e}")
            failed += 1
    
    await message.answer(f"✅ Готово! Успешно: {success}, Не удалось: {failed}")