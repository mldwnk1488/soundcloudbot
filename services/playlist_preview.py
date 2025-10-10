import yt_dlp
import re
from aiogram import types
from io import BytesIO
import requests
import asyncio
from lang_bot.translations import get_text

class PlaylistPreview:
    async def get_content_info(self, url, message=None, lang="ua"):
        """Получаю информацию о контенте (трек или плейлист) и КЭШИРУЕМ"""
        try:
            # ОТПРАВЛЯЕМ СООБЩЕНИЕ "ПОЛУЧАЮ ИНФОРМАЦИЮ"
            if message:
                loading_msg = await message.answer(get_text(lang, "getting_info"))
            
            # ПРОВЕРЯЕМ КЭШ ПЕРЕД ПАРСИНГОМ
            db = self.get_db()
            if db:
                cached_playlist, cached_tracks = await db.get_cached_playlist(url)
                if cached_playlist:
                    # ПРОВЕРЯЕМ ЧТО В КЭШЕ ЕСТЬ ВСЕ НУЖНЫЕ КЛЮЧИ
                    required_keys = ['type', 'title', 'cover_url', 'track_count', 'user']
                    for key in required_keys:
                        if key not in cached_playlist:
                            break
                    else:
                        # УДАЛЯЕМ СООБЩЕНИЕ "ПОЛУЧАЮ ИНФОРМАЦИЮ" ЕСЛИ ИСПОЛЬЗУЕМ КЭШ
                        if message:
                            await loading_msg.delete()
                        return cached_playlist
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'ignoreerrors': True,
            }
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None, 
                lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False)
            )
            
            # УДАЛЯЕМ СООБЩЕНИЕ "ПОЛУЧАЮ ИНФОРМАЦИЮ" ПОСЛЕ ПОЛУЧЕНИЯ ДАННЫХ
            if message:
                await loading_msg.delete()
            
            # ЕСЛИ ПРИВАТНЫЙ ПЛЕЙЛИСТ - ВОЗВРАЩАЕМ ОШИБКУ
            if not info:
                return {
                    'type': 'error',
                    'title': 'Приватный плейлист',
                    'track_count': 0,
                    'user': 'Недоступно',
                    'error': 'Это приватный плейлист, скачать нельзя'
                }
                
            # ЛУЧШЕЕ ОПРЕДЕЛЕНИЕ ТИПА КОНТЕНТА
            if info.get('_type') == 'playlist':
                content_type = "playlist"
                track_count = len(info.get('entries', []))
            elif 'entries' in info and len(info['entries']) > 1:
                content_type = "playlist" 
                track_count = len(info['entries'])
            else:
                content_type = "track"
                track_count = 1
            
            # получаю обложку
            cover_url = info.get('thumbnail', '')
            if not cover_url and info.get('entries'):
                first_track = info['entries'][0]
                cover_url = first_track.get('thumbnail', '')
            elif not cover_url:
                cover_url = info.get('thumbnail', '')
            
            # ДОБАВИЛ ЗАГЛУШКУ ДЛЯ YOUTUBE MUSIC
            if not cover_url or 'music.youtube.com' in url:
                # Стильные заглушки для YouTube Music
                cover_url = 'https://i.imgur.com/3Q7Yc7Q.png'  # нейтральная картинка
            
            # ОЧИСТКА НАЗВАНИЯ ОТ МУСОРА
            raw_title = info.get('title', '')
            clean_title = self.clean_filename(raw_title)
            
            # ГАРАНТИРУЕМ ЧТО ВСЕ КЛЮЧИ БУДУТ В СЛОВАРЕ
            content_info = {
                'type': content_type,
                'title': clean_title,
                'cover_url': cover_url,
                'track_count': track_count,
                'user': info.get('uploader', get_text('ua', 'unknown_artist')),
                'duration': info.get('duration', 0),
            }

            # ДОБАВЛЯЕМ ИНФОРМАЦИЮ ДЛЯ YOUTUBE MUSIC
            if 'music.youtube.com' in url:
                # YouTube Music - минимальная информация
                if not content_info['user'] or content_info['user'] in ['Unknown', '']:
                    content_info['user'] = 'YouTube Music'
                if not content_info['title'] or content_info['title'] in ['Unknown', '']:
                    content_info['title'] = f'YouTube Music ({track_count} треков)'
        
            # КЭШИРУЕМ ДАННЫЕ
            if db:
                tracks_data = []
                if content_type == "playlist":
                    tracks_data = [{'title': track.get('title', '')} for track in info.get('entries', [])]
                else:
                    tracks_data = [{'title': info.get('title', '')}]
                
                await db.cache_playlist(url, content_info, tracks_data)
            
            return content_info
            
        except Exception as e:
            # УДАЛЯЕМ СООБЩЕНИЕ "ПОЛУЧАЮ ИНФОРМАЦИЮ" ПРИ ОШИБКЕ
            if message:
                try:
                    await loading_msg.delete()
                except:
                    pass
            return None

    async def send_content_preview(self, message: types.Message, url: str, lang: str = "ua"):
        """Быстро отправляет превью и возвращает информацию для загрузки"""
        try:
            # получаю информацию о контенте с сообщением о загрузке
            content_info = await self.get_content_info(url, message, lang)
            
            if not content_info:
                # заглушка если не получилось
                content_info = {
                    'type': 'unknown',
                    'title': get_text(lang, 'unknown_playlist'),
                    'track_count': 0,
                    'user': get_text(lang, 'unknown_artist')
                }
            
            # ГАРАНТИРУЕМ ЧТО ВСЕ КЛЮЧИ ЕСТЬ
            content_info.setdefault('user', get_text(lang, 'unknown_artist'))
            content_info.setdefault('title', get_text(lang, 'unknown_playlist'))
            content_info.setdefault('track_count', 0)
            content_info.setdefault('type', 'unknown')
            
            # ЕСЛИ ОШИБКА - СРАЗУ ВОЗВРАЩАЕМ
            if content_info.get('type') == 'error':
                await message.answer(f"❌ {content_info.get('error', 'Ошибка загрузки')}")
                return {
                    'type': 'error',
                    'title': content_info['title'],
                    'user': content_info['user'],
                    'track_count': 0
                }
            
            # Очищаем название
            clean_title = self.clean_text(content_info['title'])
            clean_user = self.clean_text(content_info['user'])
            
            # ФОРМИРУЕМ ПРАВИЛЬНУЮ ПОДПИСЬ В ЗАВИСИМОСТИ ОТ ТИПА
            if content_info['type'] == "track":
                caption = f"🎵 **Трек**\n"
                caption += f"📀 **Название:** {clean_title}\n"
                caption += f"👤 **Исполнитель:** {clean_user}\n"
                
                # Добавляем длительность если есть
                if content_info.get('duration'):
                    minutes = content_info['duration'] // 60
                    seconds = content_info['duration'] % 60
                    caption += f"⏱ **Длительность:** {minutes}:{seconds:02d}\n"
            else:
                caption = f"🎵 **Плейлист**\n"
                caption += f"📁 **Название:** {clean_title}\n"
                caption += f"👤 **Автор:** {clean_user}\n"
                caption += f"📊 **Треков:** {content_info['track_count']}"
            
            # Если есть обложка - отправляем с обложкой
            if content_info.get('cover_url'):
                try:
                    response = requests.get(content_info['cover_url'], timeout=3)
                    if response.status_code == 200:
                        cover_photo = BytesIO(response.content)
                        cover_photo.name = 'cover.jpg'
                        
                        await message.answer_photo(
                            photo=cover_photo,
                            caption=caption,
                            parse_mode="Markdown"
                        )
                    else:
                        await message.answer(caption, parse_mode="Markdown")
                except Exception:
                    await message.answer(caption, parse_mode="Markdown")
            else:
                await message.answer(caption, parse_mode="Markdown")
            
            # Возвращаем информацию для загрузки
            return {
                'type': content_info['type'],
                'title': clean_title,
                'user': clean_user,
                'track_count': content_info['track_count']
            }
            
        except Exception as e:
            # заглушка если не получилось получить инфу
            return {
                'type': 'unknown',
                'title': get_text(lang, 'unknown_playlist'),
                'user': get_text(lang, 'unknown_artist'),
                'track_count': 0
            }

    def clean_text(self, text):
        """Очищает текст от невидимых символов"""
        if not text:
            return get_text('ua', 'unknown')
        
        cleaned = ''.join(char for char in text if char.isprintable())
        cleaned = ' '.join(cleaned.split())
        
        return cleaned if cleaned else get_text('ua', 'unknown')

    def clean_filename(self, filename):
        """Очищает название файла от нежелательных символов"""
        if not filename:
            return get_text('ua', 'unknown')
        
        # Убираем временные метки, даты и прочий мусор
        cleaned = re.sub(r'\s*-\s*\d+:\d+:\d+', '', filename)  # Убирает " - 5:27:16"
        cleaned = re.sub(r'\s*\d+\.\d+\s*[AP]M', '', cleaned)  # Убирает "9.24 PM"
        cleaned = re.sub(r'\s*\d{1,2}:\d{2}\s*', '', cleaned)  # Убирает "02:50"
        cleaned = re.sub(r'\s*[\d\.]+\s*[M]B', '', cleaned)    # Убирает "3.8 MB"
        
        # Убираем специальные символы
        cleaned = re.sub(r'[<>:"/\\|?*]', '', cleaned)
        
        # Обрезаем слишком длинные названия
        cleaned = cleaned.strip()
        if len(cleaned) > 50:
            cleaned = cleaned[:47] + "..."
        
        return cleaned if cleaned else get_text('ua', 'unknown')
    
    def set_db(self, db_instance):
        """Устанавливаем базу данных для кэширования"""
        self.db = db_instance
    
    def get_db(self):
        """Получаем базу данных"""
        return getattr(self, 'db', None)

playlist_preview = PlaylistPreview()