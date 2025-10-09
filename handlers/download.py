import os
import tempfile
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from services import queue_manager, downloader, file_processor, playlist_preview
from keyboards.main import get_download_keyboard
from keyboards.confirm import get_confirm_keyboard  # <-- ДОБАВИЛ
from utils.helpers import send_message_to_user, send_document_to_user, send_ad_message
from lang_bot.translations import get_text
from bot_data import get_db

router = Router()

# Функция для проверки что это ссылка
def is_valid_url(text):
    return text.startswith(('http://', 'https://', 'soundcloud.com/'))

@router.message(F.text)
async def playlist_handler(message: Message, state: FSMContext):
    url = message.text.strip()
    user_id = message.from_user.id
    
    # ПРОВЕРЯЕМ ЧТО ЭТО ССЫЛКА, А НЕ "ДА"
    if not is_valid_url(url):
        # Если это не ссылка - игнорируем
        return
    
    db = get_db()
    lang = await db.get_user_language(user_id)
    
    # 🔥 ФИЧА: ПРОВЕРЯЕМ ИСТОРИЮ
    if await db.is_playlist_downloaded(user_id, url):
        # Сохраняем URL для подтверждения
        queue_manager.user_data[user_id] = {
            'url': url, 
            'need_confirm': True,
            'language': lang
        }
        
        # Отправляем сообщение с кнопками
        await message.answer(
            "📋 Этот плейлист уже скачивали. Скачать снова?",
            reply_markup=get_confirm_keyboard(lang)
        )
        return
    
    # Дальше обычная логика...
    playlist_data, tracks_data = await db.get_cached_playlist(url)
    if playlist_data:
        await message.answer("⚡ Используем кэшированные данные...")
        playlist_info = playlist_data
    else:
        playlist_info = await playlist_preview.send_playlist_preview(message, url, lang)
    
    queue_manager.user_data[user_id] = {
        'url': url,
        'playlist_title': playlist_info['title'],
        'language': lang
    }
    
    await message.answer(get_text(lang, "choose_format"), reply_markup=get_download_keyboard(lang))

# 🔥 ДОБАВИЛ НОВЫЕ ОБРАБОТЧИКИ ДЛЯ КНОПОК ПОДТВЕРЖДЕНИЯ
@router.callback_query(F.data == "confirm_redownload")
async def confirm_redownload(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_info = queue_manager.user_data.get(user_id)
    
    if not user_info or not user_info.get('need_confirm'):
        await callback.answer("❌ Ошибка: данные не найдены")
        return
    
    # Убираем флаг подтверждения
    user_info['need_confirm'] = False
    url = user_info['url']
    lang = user_info.get('language', 'ua')
    
    # Получаем информацию о плейлисте для показа
    playlist_info = await playlist_preview.send_playlist_preview(callback.message, url, lang)
    
    # Обновляем данные
    user_info['playlist_title'] = playlist_info['title']
    
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
    
    await callback.message.edit_text("❌ Отменено")
    await callback.answer()

# Старый обработчик выбора формата (остается без изменений)
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
        await callback.answer("❌ Сначала подтвердите загрузку")
        return
    
    # Дальше обычная логика добавления в очередь...
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
    from services import queue_manager, downloader, file_processor
    from utils.helpers import send_message_to_user, send_document_to_user, send_ad_message
    from lang_bot.translations import get_text
    from bot_data import get_db  # <-- ДОБАВИЛ
    
    while queue_manager.download_queue:
        queue_manager.processing = True
        user_id, callback_data, user_info = queue_manager.download_queue[0]
        
        db = get_db()  # <-- ИСПРАВИЛ
        lang = await db.get_user_language(user_id)
        
        try:
            url = user_info['url']
            playlist_title = user_info['playlist_title']
            
            queue_manager.queue_status[user_id] = "processing"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                if callback_data == "download_zip":
                    zip_parts = []
                    try:
                        await send_message_to_user(bot, user_id, get_text(lang, "start_downloading"))
                        print(f"📥 Скачиваю плейлист: {playlist_title}")
                        
                        playlist_data, tracks_data = await db.get_cached_playlist(url)
                        if tracks_data:
                            print("⚡ Используем кэшированные треки")
                        
                        await downloader.download_playlist(url, tmpdir)
                        
                        files = file_processor.get_files_in_directory(tmpdir)
                        print(f"🔍 Найдено файлов в папке: {len(files)}")
                        if not files:
                            await send_message_to_user(bot, user_id, get_text(lang, "download_failed"))
                            continue
                        
                        await send_message_to_user(bot, user_id, get_text(lang, "packing_zip"))
                        zip_base_path = os.path.join(tempfile.gettempdir(), playlist_title)
                        
                        zip_parts = file_processor.create_zip_parts(tmpdir, zip_base_path)
                        if not zip_parts:
                            await send_message_to_user(bot, user_id, "❌ Не удалось создать архив")
                            continue
                        
                        total_parts = len(zip_parts)
                        await send_message_to_user(bot, user_id, f"📦 Отправляю архив ({total_parts} частей)...")
                        
                        total_size_mb = 0
                        
                        for part_num, part_path in enumerate(zip_parts, 1):
                            if not os.path.exists(part_path):
                                print(f"❌ Часть {part_num} не найдена: {part_path}")
                                continue
                                
                            file_size = os.path.getsize(part_path)
                            total_size_mb += file_size / 1024 / 1024
                            part_filename = f"{playlist_title}.part{part_num:03d}.zip"
                            
                            print(f"🔄 Отправляю часть {part_num}/{total_parts}: {part_path}")
                            await send_message_to_user(bot, user_id, f"📤 Отправляю часть {part_num}/{total_parts}...")
                            
                            try:
                                await send_document_to_user(
                                    bot, user_id, 
                                    FSInputFile(part_path, filename=part_filename),
                                    caption=f"🎵 {playlist_title} (часть {part_num}/{total_parts})"
                                )
                                print(f"✅ Часть {part_num} отправлена!")
                                
                            except Exception as send_error:
                                print(f"❌ Ошибка отправки части {part_num}: {send_error}")
                                await send_message_to_user(bot, user_id, f"❌ Ошибка отправки части {part_num}")
                        
                        await db.add_download_history(
                            user_id, url, playlist_title, 
                            len(files), total_size_mb
                        )
                        await db.add_statistics(
                            user_id, 'download', len(files), total_size_mb
                        )
                        
                        playlist_data = {'title': playlist_title, 'track_count': len(files)}
                        await db.cache_playlist(url, playlist_data, [])
                        
                        await send_message_to_user(bot, user_id, f"✅ Все части архива отправлены! ({total_parts} шт.)")
                        
                        stats = await db.get_user_statistics(user_id)
                        if stats and stats[0]:
                            total_downloads, total_tracks, total_size = stats
                            await send_message_to_user(
                                bot, user_id, 
                                f"📊 Ваша статистика:\n"
                                f"• Загрузок: {total_downloads}\n"
                                f"• Треков: {total_tracks}\n"
                                f"• Общий размер: {total_size:.1f} MB"
                            )
                        
                        await send_ad_message(bot, user_id, lang)
                        
                    except Exception as e:
                        print(f"❌ Ошибка в процессе ZIP: {e}")
                        await send_message_to_user(bot, user_id, f"❌ {get_text(lang, 'error')}: {e}")
                    
                    finally:
                        for part_path in zip_parts:
                            if part_path and os.path.exists(part_path):
                                os.remove(part_path)
                                print(f"🧹 Удален временный файл: {part_path}")
                
                elif callback_data == "download_tracks":
                    try:
                        await send_message_to_user(bot, user_id, get_text(lang, "start_downloading"))
                        print(f"📥 Скачиваю плейлист: {playlist_title}")
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
                                    f"📥 Скачано {idx}/{total_tracks} треков"
                                )
                            
                            await send_document_to_user(
                                bot, user_id,
                                FSInputFile(file_path), 
                                caption=f"🎵 {playlist_title} - {get_text(lang, 'track')} {idx}/{total_tracks}"
                            )
                        
                        await db.add_download_history(
                            user_id, url, playlist_title, 
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