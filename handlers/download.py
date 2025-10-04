import os
import tempfile
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile

from services.queue_manager import queue_manager
from services.downloader import downloader
from services.file_processor import file_processor
from keyboards.main import get_download_keyboard
from utils.helpers import send_message_to_user, send_document_to_user, send_ad_message

router = Router()

@router.message(F.text)
async def playlist_handler(message: Message):
    url = message.text.strip()
    user_id = message.from_user.id
    
    # Получаю название плейлиста и сохраняем данные
    playlist_title = downloader.get_playlist_title(url)
    queue_manager.user_data[user_id] = {
        'url': url,
        'playlist_title': playlist_title
    }
    
    await message.answer("выбери формат загрузки:", reply_markup=get_download_keyboard())

@router.callback_query(F.data.in_(["download_zip", "download_tracks"]))
async def callback_download(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_info = queue_manager.user_data.get(user_id)
    
    if not user_info:
        await callback.message.answer("сначала отправь ссылку на плейлист.")
        return

    # Добавляем в очередь
    queue_manager.add_to_queue(user_id, callback.data, user_info)
    pos = len(queue_manager.download_queue)
    
    if pos == 1 and not queue_manager.processing:
        await callback.message.answer(
            f"поздравляю ты первый ща все сделаю...\n\n"
            f"плейлист: {user_info['playlist_title']}\n"
            f"формат: {'ZIP-архив' if callback.data == 'download_zip' else 'отдельные треки'}"
        )
        asyncio.create_task(process_queue(callback.bot))
    else:
        await callback.message.answer(
            f"ты в очереди погоди\n\n"
            f"номер очереди: {pos}\n"
            f"плейлист: {user_info['playlist_title']}\n"
            f"формат: {'ZIP-архив' if callback.data == 'download_zip' else 'отдельные треки'}\n\n"
            f"я скажу когда начну скачивать\n"
            f"используй /queue чтобы проверить номер очереди"
        )

async def process_queue(bot):
    """Обрабатываю очередь заданий"""
    from services.queue_manager import queue_manager
    from services.downloader import downloader
    from services.file_processor import file_processor
    from utils.helpers import send_message_to_user, send_document_to_user, send_ad_message
    
    while queue_manager.download_queue:
        queue_manager.processing = True
        user_id, callback_data, user_info = queue_manager.download_queue[0]
        
        try:
            url = user_info['url']
            playlist_title = user_info['playlist_title']
            
            # Обновляем статус для пользователя
            queue_manager.queue_status[user_id] = "processing"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                if callback_data == "download_zip":
                    zip_path = None
                    try:
                        # Скачиваю треки
                        await send_message_to_user(bot, user_id, "ща скачаю...")
                        await downloader.download_playlist(url, tmpdir)
                        
                        files = file_processor.get_files_in_directory(tmpdir)
                        if not files:
                            await send_message_to_user(bot, user_id, "не удалось скачать треки.")
                            continue
                        
                        # Создаю ZIP с названием плейлиста
                        await send_message_to_user(bot, user_id, "ща упакую почекай...")
                        zip_filename = f"{playlist_title}.zip"
                        zip_path = os.path.join(tempfile.gettempdir(), zip_filename)
                        file_processor.create_zip(tmpdir, zip_path)
                        
                        # Отправляю архив с правильным именем
                        await send_message_to_user(bot, user_id, "отправляю архив...")
                        await send_document_to_user(
                            bot, user_id, 
                            FSInputFile(zip_path, filename=zip_filename),
                            caption=f"🎵 {playlist_title}"
                        )
                        
                        await send_message_to_user(bot, user_id, "ЧЕТКО!!! держи")
                        
                        # Отправляю рекламу после успешной отправки
                        await send_ad_message(bot, user_id)
                        
                    except Exception as e:
                        await send_message_to_user(bot, user_id, f"ошибка: {e}")
                    
                    finally:
                        # Удаляю временный ZIP файл
                        if zip_path and os.path.exists(zip_path):
                            os.remove(zip_path)
                
                elif callback_data == "download_tracks":
                    try:
                        await send_message_to_user(bot, user_id, "ща скачаю...")
                        await downloader.download_playlist(url, tmpdir)
                        
                        files = file_processor.get_files_in_directory(tmpdir)
                        if not files:
                            await send_message_to_user(bot, user_id, "не удалось скачать треки.")
                            continue
                        
                        # Отправляю треки по одному
                        await send_message_to_user(bot, user_id, f"ща отправлю {len(files)} треков...")
                        for idx, file_name in enumerate(files, 1):
                            file_path = os.path.join(tmpdir, file_name)
                            await send_document_to_user(
                                bot, user_id,
                                FSInputFile(file_path), 
                                caption=f"🎵 {playlist_title} - трек {idx}/{len(files)}"
                            )
                        
                        await send_message_to_user(bot, user_id, "все треки отправил")
                        
                        # Отправляю рекламу после успешной отправки всех треков
                        await send_ad_message(bot, user_id)
                        
                    except Exception as e:
                        await send_message_to_user(bot, user_id, f"ОШИБКА ВТФ: {e}")
        
        except Exception as e:
            await send_message_to_user(bot, user_id, f"фатальная ошибка: {e}")
        
        finally:
            # Удаляю задание из очереди и статуса
            if queue_manager.download_queue:
                queue_manager.download_queue.popleft()
            queue_manager.remove_from_queue(user_id)
    
    queue_manager.processing = False