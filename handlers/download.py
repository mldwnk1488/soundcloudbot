import os
import tempfile
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from services import queue_manager, downloader, file_processor, playlist_preview
from keyboards.main import get_download_keyboard
from utils.helpers import send_message_to_user, send_document_to_user, send_ad_message
from lang_bot.translations import get_text
from bot_data import get_db

router = Router()

def is_valid_url(text):
    return text.startswith(('http://', 'https://', 'soundcloud.com/', 'youtube.com/', 'youtu.be/', 'music.youtube.com/'))

@router.message(F.text)
async def playlist_handler(message: Message, state: FSMContext):
    url = message.text.strip()
    user_id = message.from_user.id
    
    if not is_valid_url(url):
        return
    
    db = get_db()
    lang = await db.get_user_language(user_id)
    
    # ДОБАВЛЯЕМ ПРЕДУПРЕЖДЕНИЕ ДЛЯ YOUTUBE
    if any(domain in url for domain in ['youtube.com', 'youtu.be', 'music.youtube.com']):
        await message.answer(get_text(lang, "youtube_slow_warning"))
    
    # 🔥 ПРОВЕРЯЕМ ЧТО ЮЗЕР УЖЕ НЕ В ОЧЕРЕДИ
    if queue_manager.is_user_in_queue(user_id):
        await message.answer("⏳ Ты уже в очереди! Дождись завершения текущей загрузки.")
        return
    
    content_info = await playlist_preview.send_content_preview(message, url, lang)

    if content_info.get('type') == 'error':
        await message.answer(f"❌ {content_info.get('error', 'Ошибка загрузки')}")
        return

    queue_manager.user_data[user_id] = {
        'url': url,
        'content_type': content_info['type'],
        'playlist_title': content_info['title'],
        'language': lang
    }

    await message.answer(get_text(lang, "choose_format"), reply_markup=get_download_keyboard(lang))

@router.callback_query(F.data.in_(["download_zip", "download_tracks"]))
async def callback_download(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_info = queue_manager.user_data.get(user_id)
    
    if not user_info:
        db = get_db()
        lang = await db.get_user_language(user_id)
        await callback.message.answer(get_text(lang, "send_link_first"))
        return

    db = get_db()
    lang = await db.get_user_language(user_id)
    
    # 🔥 ПРОВЕРЯЕМ ЧТО ЮЗЕР УЖЕ НЕ В ОЧЕРЕДИ
    if queue_manager.is_user_in_queue(user_id):
        await callback.answer("⏳ Ты уже в очереди!", show_alert=True)
        return
    
    content_type = user_info.get('content_type', 'playlist')
    content_type_text = get_text(lang, "track") if content_type == 'track' else get_text(lang, "playlist")
    
    # 🔥 ДОБАВЛЯЕМ В ОЧЕРЕДЬ И ПРОВЕРЯЕМ УСПЕХ
    added = await queue_manager.add_to_queue(user_id, callback.data, user_info)
    
    if not added:
        await callback.answer("❌ Ты уже в очереди!", show_alert=True)
        return
    
    pos = len(queue_manager.download_queue)
    
    if pos == 1 and not queue_manager.processing:
        format_text = get_text(lang, "zip_format") if callback.data == "download_zip" else get_text(lang, "tracks_format")
        await callback.message.answer(
            f"🎉 {get_text(lang, 'congrats_first')}\n\n"
            f"📁 {content_type_text}: {user_info['playlist_title']}\n"
            f"🗂 {get_text(lang, 'format')}: {format_text}"
        )
        asyncio.create_task(process_queue(callback.bot))
    else:
        format_text = get_text(lang, "zip_format") if callback.data == "download_zip" else get_text(lang, "tracks_format")
        await callback.message.answer(
            f"⏳ {get_text(lang, 'you_in_queue')}\n\n"
            f"📊 {get_text(lang, 'queue_position')}: {pos}\n"
            f"📁 {content_type_text}: {user_info['playlist_title']}\n"
            f"📦 {get_text(lang, 'format')}: {format_text}"
        )
    
    await callback.answer()

async def process_queue(bot):
    from services import queue_manager, downloader, file_processor
    from utils.helpers import send_message_to_user, send_document_to_user, send_ad_message
    from lang_bot.translations import get_text
    from bot_data import get_db
    
    # 🔥 ЗАПРЕЩАЕМ ПАРАЛЛЕЛЬНЫЙ ПРОЦЕССИНГ
    if queue_manager.processing:
        return
        
    queue_manager.processing = True
    
    try:
        while True:
            # 🔥 БЕЗОПАСНО ПОЛУЧАЕМ СЛЕДУЮЩЕГО ЮЗЕРА
            next_task = await queue_manager.process_next()
            if not next_task:
                break
                
            user_id, callback_data, user_info = next_task
            
            db = get_db()
            lang = await db.get_user_language(user_id)
            
            try:
                url = user_info['url']
                content_title = user_info['playlist_title']
                
                await send_message_to_user(bot, user_id, get_text(lang, "start_downloading"))
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    success = await downloader.download_playlist(url, tmpdir)
                    
                    if not success:
                        await send_message_to_user(bot, user_id, "❌ Не удалось скачать треки")
                        continue
                    
                    files = file_processor.get_files_in_directory(tmpdir)
                    if not files:
                        await send_message_to_user(bot, user_id, "❌ Файлы не найдены")
                        continue
                    
                    if callback_data == "download_zip":
                        await send_message_to_user(bot, user_id, get_text(lang, "packing_zip"))
                        zip_base_path = os.path.join(tempfile.gettempdir(), content_title)
                        
                        zip_parts = file_processor.create_zip_parts(tmpdir, zip_base_path)
                        if not zip_parts:
                            await send_message_to_user(bot, user_id, "❌ Не удалось создать архив")
                            continue
                        
                        total_parts = len(zip_parts)
                        await send_message_to_user(bot, user_id, get_text(lang, "sending_archive").format(parts=total_parts))
                        
                        for part_num, part_path in enumerate(zip_parts, 1):
                            if not os.path.exists(part_path):
                                continue
                                
                            part_filename = f"{content_title}.part{part_num:03d}.zip"
                            
                            try:
                                await send_document_to_user(
                                    bot, user_id, 
                                    FSInputFile(part_path, filename=part_filename),
                                    caption=get_text(lang, "part_sent").format(
                                        title=content_title, 
                                        current=part_num, 
                                        total=total_parts
                                    )
                                )
                                os.remove(part_path)
                                
                            except Exception:
                                await send_message_to_user(bot, user_id, f"❌ Ошибка отправки части {part_num}")
                        
                        await send_message_to_user(bot, user_id, get_text(lang, "archive_sent").format(parts=total_parts))
                    
                    elif callback_data == "download_tracks":
                        total_tracks = len(files)
                        await send_message_to_user(bot, user_id, f"📤 {get_text(lang, 'sending_tracks')} {total_tracks}...")
                        
                        for idx, file_name in enumerate(files, 1):
                            file_path = os.path.join(tmpdir, file_name)
                            await send_document_to_user(
                                bot, user_id,
                                FSInputFile(file_path), 
                                caption=f"🎵 {content_title} - {get_text(lang, 'track')} {idx}/{total_tracks}"
                            )
                        
                        await send_message_to_user(bot, user_id, get_text(lang, "all_tracks_sent"))
                    
                    await send_ad_message(bot, user_id, lang)
            
            except Exception as e:
                print(f"❌ Ошибка в очереди: {e}")
                await send_message_to_user(bot, user_id, f"❌ Ошибка: {str(e)}")
            
            finally:
                # 🔥 БЕЗОПАСНО ЗАВЕРШАЕМ ТЕКУЩУЮ ЗАДАЧУ
                await queue_manager.complete_current()
    
    finally:
        queue_manager.processing = False