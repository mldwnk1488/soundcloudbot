import os
import tempfile
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext  # ← ДОБАВИТЬ ЭТОТ ИМПОРТ

from services import queue_manager, downloader, file_processor, playlist_preview
from keyboards.main import get_download_keyboard
from utils.helpers import send_message_to_user, send_document_to_user, send_ad_message
from lang_bot.translations import get_text

router = Router()

@router.message(F.text)
async def playlist_handler(message: Message, state: FSMContext):
    url = message.text.strip()
    user_id = message.from_user.id
    
    # Получаем язык пользователя из queue_manager
    lang = queue_manager.user_languages.get(user_id, 'ua')
    
    # 1. сначала отправляем информацию
    playlist_data = await playlist_preview.send_playlist_preview(message, url, lang)
    
    # 2. сохраняю данные для загрузки
    queue_manager.user_data[user_id] = {
        'url': url,
        'playlist_title': playlist_data['title'],
        'language': lang  # ← сохраняем язык
    }
    
    # 3. затем отправляю выбор формата загрузки
    await message.answer(get_text(lang, "choose_format"), reply_markup=get_download_keyboard(lang))

@router.callback_query(F.data.in_(["download_zip", "download_tracks"]))
async def callback_download(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_info = queue_manager.user_data.get(user_id)
    
    if not user_info:
        # Получаем язык из queue_manager
        lang = queue_manager.user_languages.get(user_id, 'ua')
        await callback.message.answer(get_text(lang, "send_link_first"))
        return

    # Получаем язык из queue_manager
    lang = queue_manager.user_languages.get(user_id, 'ua')
    
    # Добавляем в очередь
    queue_manager.add_to_queue(user_id, callback.data, user_info)
    pos = len(queue_manager.download_queue)
    
    if pos == 1 and not queue_manager.processing:
        format_text = get_text(lang, "zip_format") if callback.data == "download_zip" else get_text(lang, "tracks_format")
        await callback.message.answer(
            f"🎉 {get_text(lang, 'congrats_first')}\n\n"
            f"📁 {get_text(lang, 'playlist')}: {user_info['playlist_title']}\n"
            f"🗂 {get_text(lang, 'format')}: {format_text}"
        )
        asyncio.create_task(process_queue(callback.bot))
    else:
        format_text = get_text(lang, "zip_format") if callback.data == "download_zip" else get_text(lang, "tracks_format")
        await callback.message.answer(
            f"⏳ {get_text(lang, 'you_in_queue')}\n\n"
            f"📊 {get_text(lang, 'queue_position')}: {pos}\n"
            f"📁 {get_text(lang, 'playlist')}: {user_info['playlist_title']}\n"
            f"📦 {get_text(lang, 'format')}: {format_text}\n\n"
            f"🔔 {get_text(lang, 'will_notify_start')}\n"
            f"📋 {get_text(lang, 'use_queue_command')}"
        )

async def process_queue(bot):
    """Обрабатываю очередь заданий"""
    from services import queue_manager, downloader, file_processor
    from utils.helpers import send_message_to_user, send_document_to_user, send_ad_message
    from lang_bot.translations import get_text
    
    while queue_manager.download_queue:
        queue_manager.processing = True
        user_id, callback_data, user_info = queue_manager.download_queue[0]
        
        # Получаем язык пользователя из сохраненных данных
        lang = user_info.get('language', 'ua')
        
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
                        await send_message_to_user(bot, user_id, get_text(lang, "start_downloading"))
                        await downloader.download_playlist(url, tmpdir)
                        
                        files = file_processor.get_files_in_directory(tmpdir)
                        if not files:
                            await send_message_to_user(bot, user_id, get_text(lang, "download_failed"))
                            continue
                        
                        # Создаю ZIP с названием плейлиста
                        await send_message_to_user(bot, user_id, get_text(lang, "packing_zip"))
                        zip_filename = f"{playlist_title}.zip"
                        zip_path = os.path.join(tempfile.gettempdir(), zip_filename)
                        file_processor.create_zip(tmpdir, zip_path)
                        
                        # Отправляю архив с правильным именем
                        await send_message_to_user(bot, user_id, get_text(lang, "sending_file"))
                        await send_document_to_user(
                            bot, user_id, 
                            FSInputFile(zip_path, filename=zip_filename),
                            caption=f"🎵 {playlist_title}"
                        )
                        
                        await send_message_to_user(bot, user_id, get_text(lang, "done_zip"))
                        
                        # Отправляю рекламу после успешной отправки
                        await send_ad_message(bot, user_id, lang)
                        
                    except Exception as e:
                        await send_message_to_user(bot, user_id, f"❌ {get_text(lang, 'error')}: {e}")
                    
                    finally:
                        # Удаляю временный ZIP файл
                        if zip_path and os.path.exists(zip_path):
                            os.remove(zip_path)
                
                elif callback_data == "download_tracks":
                    try:
                        await send_message_to_user(bot, user_id, get_text(lang, "start_downloading"))
                        await downloader.download_playlist(url, tmpdir)
                        
                        files = file_processor.get_files_in_directory(tmpdir)
                        if not files:
                            await send_message_to_user(bot, user_id, get_text(lang, "download_failed"))
                            continue
                        
                        # Отправляю треки по одному
                        await send_message_to_user(bot, user_id, f"📤 {get_text(lang, 'sending_tracks')} {len(files)}...")
                        for idx, file_name in enumerate(files, 1):
                            file_path = os.path.join(tmpdir, file_name)
                            await send_document_to_user(
                                bot, user_id,
                                FSInputFile(file_path), 
                                caption=f"🎵 {playlist_title} - {get_text(lang, 'track')} {idx}/{len(files)}"
                            )
                        
                        await send_message_to_user(bot, user_id, get_text(lang, "all_tracks_sent"))
                        
                        # Отправляю рекламу после успешной отправки всех треков
                        await send_ad_message(bot, user_id, lang)
                        
                    except Exception as e:
                        await send_message_to_user(bot, user_id, f"❌ {get_text(lang, 'error')}: {e}")
        
        except Exception as e:
            await send_message_to_user(bot, user_id, f"❌ {get_text(lang, 'fatal_error')}: {e}")
        
        finally:
            # Удаляю задание из очереди и статуса
            if queue_manager.download_queue:
                queue_manager.download_queue.popleft()
            queue_manager.remove_from_queue(user_id)
    
    queue_manager.processing = False