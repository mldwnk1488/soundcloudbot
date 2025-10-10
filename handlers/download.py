import os
import tempfile
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from services import queue_manager, downloader, file_processor, playlist_preview
from keyboards.main import get_download_keyboard
from keyboards.confirm import get_confirm_keyboard
from utils.helpers import send_message_to_user, send_document_to_user, send_ad_message
from lang_bot.translations import get_text
from bot_data import get_db

router = Router()

# Функция для проверки что это ссылка
def is_valid_url(text):
    return text.startswith(('http://', 'https://', 'soundcloud.com/', 'youtube.com/', 'youtu.be/', 'music.youtube.com/'))

@router.message(F.text)
async def playlist_handler(message: Message, state: FSMContext):
    url = message.text.strip()
    user_id = message.from_user.id
    # УБИРАЕМ ПРИНТ
    # print(f"🔍 Получено сообщение: {url} от {user_id}")
    
    # ПРОВЕРЯЕМ ЧТО ЭТО ССЫЛКА, А НЕ "ДА"
    if not is_valid_url(url):
        # print("❌ Не валидная ссылка")
        return
    
    db = get_db()
    lang = await db.get_user_language(user_id)
    # УБИРАЕМ ПРИНТ  
    # print(f"🌐 Язык пользователя: {lang}")
    
    # ДОБАВЛЯЕМ ПРЕДУПРЕЖДЕНИЕ ДЛЯ YOUTUBE
    if any(domain in url for domain in ['youtube.com', 'youtu.be', 'music.youtube.com']):
        await message.answer(get_text(lang, "youtube_slow_warning"))
    
    # 🔥 ФИЧА: ПРОВЕРЯЕМ ИСТОРИЮ
    if await db.is_playlist_downloaded(user_id, url):
        # УБИРАЕМ ПРИНТ
        # print("📋 Плейлист уже скачивали")
        
        # Сохраняем URL для подтверждения
        queue_manager.user_data[user_id] = {
            'url': url, 
            'need_confirm': True,
            'language': lang
        }
        
        # Отправляем сообщение с кнопками
        await message.answer(
            get_text(lang, "download_again"),
            reply_markup=get_confirm_keyboard(lang)
        )
        return
    
    else:
        # УБИРАЕМ ПРИНТ
        # print("🔄 Обрабатываем новую ссылку")
        
        # Дальше обычная логика...
        playlist_data, tracks_data = await db.get_cached_playlist(url)
        if playlist_data:
            await message.answer(get_text(lang, "playlist_cached"))
            content_info = playlist_data
        else:
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
# 🔥 ДОБАВИЛ НОВЫЕ ОБРАБОТЧИКИ ДЛЯ КНОПОК ПОДТВЕРЖДЕНИЯ
@router.callback_query(F.data == "confirm_redownload")
async def confirm_redownload(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_info = queue_manager.user_data.get(user_id)
    
    if not user_info or not user_info.get('need_confirm'):
        await callback.answer("❌ " + get_text('ua', "error"))
        return
    
    # Убираем флаг подтверждения
    user_info['need_confirm'] = False
    url = user_info['url']
    lang = user_info.get('language', 'ua')
    
    # Получаем информацию о контенте для показа
    content_info = await playlist_preview.send_content_preview(callback.message, url, lang)
    
    # Обновляем данные
    user_info['content_type'] = content_info['type']
    user_info['playlist_title'] = content_info['title']
    
    # Показываем выбор формата
    await callback.message.edit_text(
        get_text(lang, "choose_format"),
        reply_markup=get_download_keyboard(lang)
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_redownload")
async def cancel_redownload(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Очищаем данные
    if user_id in queue_manager.user_data:
        del queue_manager.user_data[user_id]
    
    await callback.message.edit_text("❌ " + get_text('ua', "canceled"))
    await callback.answer()

# Обработчик выбора формата
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
    
    # 🔥 ЕСЛИ НУЖНО ПОДТВЕРЖДЕНИЕ - НЕ ДАЕМ ВЫБРАТЬ ФОРМАТ
    if user_info.get('need_confirm'):
        await callback.answer("❌ " + get_text(lang, "confirm_first"))
        return
    
    # Определяем тип контента для текста
    content_type = user_info.get('content_type', 'playlist')
    content_type_text = get_text(lang, "track") if content_type == 'track' else get_text(lang, "playlist")
    
    # Дальше обычная логика добавления в очередь...
    queue_manager.add_to_queue(user_id, callback.data, user_info)
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
            f"📦 {get_text(lang, 'format')}: {format_text}\n\n"
            f"🔔 {get_text(lang, 'will_notify_start')}\n"
            f"📋 {get_text(lang, 'use_queue_command')}"
        )

async def process_queue(bot):
    from services import queue_manager, downloader, file_processor
    from utils.helpers import send_message_to_user, send_document_to_user, send_ad_message
    from lang_bot.translations import get_text
    from bot_data import get_db
    
    while queue_manager.download_queue:
        queue_manager.processing = True
        user_id, callback_data, user_info = queue_manager.download_queue[0]
        
        db = get_db()
        lang = await db.get_user_language(user_id)
        
        try:
            url = user_info['url']
            content_title = user_info['playlist_title']
            content_type = user_info.get('content_type', 'playlist')
            
            queue_manager.queue_status[user_id] = "processing"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                if callback_data == "download_zip":
                    zip_parts = []
                    try:
                        await send_message_to_user(bot, user_id, get_text(lang, "start_downloading"))
                        print(f"📥 Скачиваю {content_type}: {content_title}")
                        
                        playlist_data, tracks_data = await db.get_cached_playlist(url)
                        if tracks_data:
                            print("⚡ " + get_text(lang, "playlist_cached"))
                        
                        await downloader.download_playlist(url, tmpdir)
                        
                        files = file_processor.get_files_in_directory(tmpdir)
                        print(f"🔍 Найдено файлов в папке: {len(files)}")
                        if not files:
                            await send_message_to_user(bot, user_id, get_text(lang, "download_failed"))
                            continue
                        
                        await send_message_to_user(bot, user_id, get_text(lang, "packing_zip"))
                        zip_base_path = os.path.join(tempfile.gettempdir(), content_title)
                        
                        zip_parts = file_processor.create_zip_parts(tmpdir, zip_base_path)
                        if not zip_parts:
                            await send_message_to_user(bot, user_id, "❌ " + get_text(lang, "archive_creation_failed"))
                            continue
                        
                        total_parts = len(zip_parts)
                        await send_message_to_user(bot, user_id, get_text(lang, "sending_archive").format(parts=total_parts))
                        
                        total_size_mb = 0
                        
                        for part_num, part_path in enumerate(zip_parts, 1):
                            if not os.path.exists(part_path):
                                print(f"❌ " + get_text(lang, "part_not_found").format(part=part_num, path=part_path))
                                continue
                                
                            file_size = os.path.getsize(part_path)
                            total_size_mb += file_size / 1024 / 1024
                            part_filename = f"{content_title}.part{part_num:03d}.zip"
                            
                            print(f"🔄 " + get_text(lang, "sending_part").format(current=part_num, total=total_parts))
                            await send_message_to_user(bot, user_id, get_text(lang, "sending_part").format(current=part_num, total=total_parts))
                            
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
                                print(f"✅ " + get_text(lang, "part_sent_success").format(part=part_num))
                                
                            except Exception as send_error:
                                print(f"❌ " + get_text(lang, "part_send_error").format(part=part_num, error=send_error))
                                await send_message_to_user(bot, user_id, f"❌ " + get_text(lang, "part_send_error").format(part=part_num, error=send_error))
                        
                        await db.add_download_history(
                            user_id, url, content_title, 
                            len(files), total_size_mb
                        )
                        await db.add_statistics(
                            user_id, 'download', len(files), total_size_mb
                        )
                        
                        content_data = {'title': content_title, 'track_count': len(files), 'type': content_type}
                        await db.cache_playlist(url, content_data, [])
                        
                        await send_message_to_user(bot, user_id, get_text(lang, "archive_sent").format(parts=total_parts))
                        
                        stats = await db.get_user_statistics(user_id)
                        if stats and stats[0]:
                            total_downloads, total_tracks, total_size = stats
                            await send_message_to_user(
                                bot, user_id, 
                                get_text(lang, "your_stats") + ":\n" +
                                get_text(lang, "total_downloads") + f": {total_downloads}\n" +
                                get_text(lang, "total_tracks") + f": {total_tracks}\n" +
                                get_text(lang, "total_size") + f": {total_size:.1f} MB"
                            )
                        
                        await send_ad_message(bot, user_id, lang)
                        
                    except Exception as e:
                        print(f"❌ " + get_text(lang, "zip_process_error").format(error=e))
                        await send_message_to_user(bot, user_id, f"❌ {get_text(lang, 'error')}: {e}")
                    
                    finally:
                        for part_path in zip_parts:
                            if part_path and os.path.exists(part_path):
                                os.remove(part_path)
                                print(f"🧹 " + get_text(lang, "temp_file_cleaned").format(path=part_path))
                
                elif callback_data == "download_tracks":
                    try:
                        await send_message_to_user(bot, user_id, get_text(lang, "start_downloading"))
                        print(f"📥 Скачиваю {content_type}: {content_title}")
                        await downloader.download_playlist(url, tmpdir)
                        
                        files = file_processor.get_files_in_directory(tmpdir)
                        if not files:
                            await send_message_to_user(bot, user_id, get_text(lang, "download_failed"))
                            continue
                        
                        total_tracks = len(files)
                        await send_message_to_user(bot, user_id, f"📤 {get_text(lang, 'sending_tracks')} {total_tracks}...")
                        
                        total_size_mb = 0
                        
                        for idx, file_name in enumerate(files, 1):
                            file_path = os.path.join(tmpdir, file_name)
                            file_size = os.path.getsize(file_path)
                            total_size_mb += file_size / 1024 / 1024
                            
                            if idx % 5 == 0 or idx == total_tracks:
                                await send_message_to_user(
                                    bot, user_id, 
                                    get_text(lang, "progress_status").format(current=idx, total=total_tracks)
                                )
                            
                            await send_document_to_user(
                                bot, user_id,
                                FSInputFile(file_path), 
                                caption=f"🎵 {content_title} - {get_text(lang, 'track')} {idx}/{total_tracks}"
                            )
                        
                        await db.add_download_history(
                            user_id, url, content_title, 
                            len(files), total_size_mb
                        )
                        await db.add_statistics(
                            user_id, 'download', len(files), total_size_mb
                        )
                        
                        await send_message_to_user(bot, user_id, get_text(lang, "all_tracks_sent"))
                        await send_ad_message(bot, user_id, lang)
                        
                    except Exception as e:
                        await send_message_to_user(bot, user_id, f"❌ {get_text(lang, 'error')}: {e}")
        
        except Exception as e:
            await send_message_to_user(bot, user_id, f"❌ {get_text(lang, 'fatal_error')}: {e}")
        
        finally:
            if queue_manager.download_queue:
                queue_manager.download_queue.popleft()
            queue_manager.remove_from_queue(user_id)
    
    queue_manager.processing = False