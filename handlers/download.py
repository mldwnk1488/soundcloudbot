import os
import tempfile
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile  # ← Убедись что это есть
from aiogram.fsm.context import FSMContext

from services import downloader, file_processor, playlist_preview
from keyboards.main import get_download_keyboard
from keyboards.confirm import get_confirm_keyboard
from utils import send_message_to_user, send_document_to_user, send_ad_message, is_valid_url, safe_db_operation
from lang_bot.translations import get_text
from core import db_manager, queue_manager

router = Router()

MAX_TRACKS_FOR_ZIP = 15
ZIP_PART_SIZE_MB = 45

@router.message(F.text)
async def playlist_handler(message: Message, state: FSMContext):
    url = message.text.strip()
    user_id = message.from_user.id
    
    if not is_valid_url(url):
        return
    
    lang = await safe_db_operation(
        lambda db: db.get_user_language(user_id),
        fallback='ua'
    )
    
    was_downloaded, prev_title, prev_date = await safe_db_operation(
        lambda db: db.is_playlist_downloaded(user_id, url),
        fallback=(False, None, None)
    )
    
    if was_downloaded:
        date_str = get_text(lang, "unknown")
        if prev_date:
            if hasattr(prev_date, 'strftime'):
                date_str = prev_date.strftime("%d.%m.%Y")
            elif isinstance(prev_date, str):
                date_str = prev_date[:10]
        
        await message.answer(
            f"📋 <b>{get_text(lang, 'already_downloaded')}</b>\n\n"
            f"🎵 <b>{prev_title}</b>\n"
            f"📅 {get_text(lang, 'downloaded_at')}: {date_str}\n\n"
            f"{get_text(lang, 'download_again')}",
            parse_mode="HTML",
            reply_markup=get_confirm_keyboard(lang)
        )   
        await state.update_data(redownload_url=url)
        return
    
    content_info = await playlist_preview.get_content_info(url, message, lang)

    if not content_info or content_info.get('type') == 'error':
        error_msg = content_info.get('title', get_text(lang, 'error')) if content_info else get_text(lang, 'error')
        await message.answer(f"❌ {error_msg}")
        return

    content_type = content_info.get('type', 'playlist')
    playlist_title = content_info.get('title', get_text(lang, 'unknown_playlist'))
    user_name = content_info.get('user', get_text(lang, 'unknown_artist'))
    track_count = content_info.get('track_count', 0)
    
    content_type_text = get_text(lang, "track") if content_type == 'track' else get_text(lang, "playlist")
    
    preview_text = (
        f"🎵 <b>{content_type_text}</b>\n"
        f"📀 <b>{get_text(lang, 'title')}:</b> {playlist_title}\n"
        f"👤 <b>{get_text(lang, 'artist')}:</b> {user_name}\n"
    )

    if content_type == 'playlist':
        preview_text += f"📊 <b>{get_text(lang, 'track_count')}:</b> {track_count}\n"

    preview_text += f"\n{get_text(lang, 'choose_format')}"

    await state.update_data({
        'url': url,
        'content_type': content_type,
        'playlist_title': playlist_title,
        'track_count': track_count
    })

    await message.answer(preview_text, parse_mode="HTML", reply_markup=get_download_keyboard(lang))

@router.callback_query(F.data == "confirm_redownload")
async def confirm_redownload(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = await state.get_data()
    url = user_data.get('redownload_url')
    
    lang = await safe_db_operation(
        lambda db: db.get_user_language(user_id),
        fallback='ua'
    )
    
    if not url:
        await callback.answer(get_text(lang, "error"), show_alert=True)
        return
    
    try:
        await callback.message.delete()
    except:
        pass
    
    content_info = await playlist_preview.get_content_info(url, callback.message, lang)
    
    if not content_info or content_info.get('type') == 'error':
        error_msg = content_info.get('error', 'Ошибка загрузки') if content_info else 'Не удалось получить информацию'
        await callback.message.answer(f"❌ {error_msg}")
        return
    
    await state.update_data({
        'url': url,
        'content_type': content_info.get('type', 'playlist'),
        'playlist_title': content_info.get('title', 'Неизвестный плейлист'),
        'track_count': content_info.get('track_count', 0),
        'is_redownload': True
    })
    
    await callback.message.answer(get_text(lang, "choose_format"), reply_markup=get_download_keyboard(lang))
    await callback.answer()

@router.callback_query(F.data == "cancel_redownload")
async def cancel_redownload(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = await safe_db_operation(
        lambda db: db.get_user_language(callback.from_user.id),
        fallback='ua'
    )
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(get_text(lang, "canceled"))
    await callback.answer()

@router.callback_query(F.data.in_(["download_zip", "download_tracks"]))
async def callback_download(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    user_data = await state.get_data()
    
    if not user_data or 'url' not in user_data:
        lang = await safe_db_operation(
            lambda db: db.get_user_language(user_id),
            fallback='ua'
        )
        await callback.message.answer(get_text(lang, "send_link_first"))
        await callback.answer()
        return

    lang = await safe_db_operation(
        lambda db: db.get_user_language(user_id),
        fallback='ua'
    )
    
    await callback.answer()
    
    if queue_manager.is_processing():
        position = await queue_manager.add_to_queue(user_id)
        
        queue_manager.set_user_data(user_id, {
            'user_data': user_data,
            'download_type': callback.data,
            'lang': lang
        })
        
        await callback.message.answer(
            f"⏳ {get_text(lang, 'you_in_queue')}\n"
            f"📊 {get_text(lang, 'queue_position')}: {position}\n"
            f"{get_text(lang, 'total_in_queue')}: {queue_manager.get_queue_size()}\n\n"
            f"💬 {get_text(lang, 'will_notify_start')}"
        )
    else:
        queue_manager.start_processing(user_id)
        await start_download(callback.bot, user_id, callback.data, user_data)

async def send_zip_parts(bot, user_id, tmpdir, content_title, lang):
    try:
        zip_base_path = os.path.join(tempfile.gettempdir(), f"{content_title}")
        
        zip_parts = file_processor.create_zip_parts(tmpdir, zip_base_path, ZIP_PART_SIZE_MB * 1024 * 1024)
        
        if not zip_parts:
            await send_message_to_user(bot, user_id, f"❌ {get_text(lang, 'archive_creation_failed')}")
            return False
        
        total_parts = len(zip_parts)
        await send_message_to_user(bot, user_id, get_text(lang, "sending_archive").format(parts=total_parts))
        
        for i, part_path in enumerate(zip_parts, 1):
            if os.path.exists(part_path):
                try:
                    await send_document_to_user(
                        bot, user_id,
                        FSInputFile(part_path),
                        caption=get_text(lang, "part_sent").format(title=content_title, current=i, total=total_parts)
                    )
                except Exception as e:
                    await send_message_to_user(bot, user_id, get_text(lang, "part_send_error").format(part=i, error=str(e)))
            else:
                await send_message_to_user(bot, user_id, get_text(lang, "part_not_found").format(part=i, path=part_path))
        
        await send_message_to_user(bot, user_id, get_text(lang, "archive_sent").format(parts=total_parts))
        
        file_processor.cleanup_zip_parts(zip_parts)
        
        return True
        
    except Exception as e:
        await send_message_to_user(bot, user_id, get_text(lang, "zip_process_error").format(error=str(e)))
        return False

async def start_download(bot, user_id, download_type, user_info):
    lang = await safe_db_operation(
        lambda db: db.get_user_language(user_id),
        fallback='ua'
    )
    
    try:
        url = user_info['url']
        content_title = user_info['playlist_title']
        
        await send_message_to_user(bot, user_id, 
            f"🎯 {get_text(lang, 'download_started')}\n\n"
            f"📁 {content_title}\n\n"
            f"⏰ {get_text(lang, 'processing')}"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            success = await downloader.download_playlist(
                url, tmpdir, 
                user_id=user_id, 
                bot=bot, 
                lang=lang,
                total_tracks=user_info.get('track_count', 0)
            )
            
            if not success:
                await send_message_to_user(bot, user_id, f"❌ {get_text(lang, 'download_failed')}")
                return
            
            files = file_processor.get_files_in_directory(tmpdir)
            if not files:
                await send_message_to_user(bot, user_id, get_text(lang, "download_failed"))
                return
            
            if download_type == "download_tracks":
                total_tracks = len(files)
                await send_message_to_user(bot, user_id, f"📤 {get_text(lang, 'sending_tracks')} {total_tracks}...")
                
                for idx, file_name in enumerate(files, 1):
                    file_path = os.path.join(tmpdir, file_name)
                    if os.path.exists(file_path):
                        await send_document_to_user(
                            bot, user_id,
                            FSInputFile(file_path), 
                            caption=f"🎵 {content_title} - {get_text(lang, 'track')} {idx}/{total_tracks}"
                        )
                
                await send_message_to_user(bot, user_id, get_text(lang, "all_tracks_sent"))
            
            elif download_type == "download_zip":
                await send_zip_parts(bot, user_id, tmpdir, content_title, lang)
            
            total_size_mb = sum(os.path.getsize(os.path.join(tmpdir, f)) / (1024 * 1024) for f in files if os.path.exists(os.path.join(tmpdir, f)))
            
            if not user_info.get('is_redownload'):
                await safe_db_operation(
                    lambda db: db.add_download_history(user_id, url, content_title, len(files), total_size_mb)
                )
                await safe_db_operation(
                    lambda db: db.add_statistics(user_id, "download", len(files), total_size_mb)
                )
            
            await send_ad_message(bot, user_id, lang)
    
    except Exception as e:
        print(f"Ошибка скачивания для user {user_id}: {e}")
        await send_message_to_user(bot, user_id, f"❌ {get_text(lang, 'error')}: {str(e)}")
    
    finally:
        queue_manager.finish_processing()
        await process_next_in_queue(bot)

async def process_next_in_queue(bot):
    if queue_manager.is_processing():
        return
        
    next_user = queue_manager.get_next_user()
    if not next_user:
        return
        
    user_data = queue_manager.get_user_data(next_user)
    if not user_data:
        print(f"Нет данных для user_id={next_user} в очереди")
        return
        
    print(f"Запускаем скачивание для user_id={next_user} из очереди")
    
    try:
        lang = user_data.get('lang', 'ua')
        await send_message_to_user(
            bot, next_user,
            f"🎉 {get_text(lang, 'congrats_first')}\n"
            f"⬇️ {get_text(lang, 'start_downloading')}"
        )
        
        queue_manager.start_processing(next_user)
        await start_download(
            bot,
            next_user,
            user_data['download_type'],
            user_data['user_data']
        )
        
    except Exception as e:
        print(f"Ошибка обработки user_id={next_user} из очереди: {e}")
        queue_manager.finish_processing()
    finally:
        queue_manager.remove_user_data(next_user)