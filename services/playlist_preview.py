import yt_dlp
from aiogram import types
from io import BytesIO
import requests
import asyncio
from lang_bot.translations import get_text

class PlaylistPreview:
    async def get_playlist_info(self, playlist_url):
        """получаю информацию о плейлисте"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None, 
                lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(playlist_url, download=False)
            )
            
            # получаю обложку из первого трека
            cover_url = info.get('thumbnail', '')
            if not cover_url and info.get('entries'):
                first_track = info['entries'][0]
                cover_url = first_track.get('thumbnail', '')
            
            playlist_info = {
                'title': info.get('title', get_text('ua', 'unknown_playlist')),
                'cover_url': cover_url,
                'track_count': len(info.get('entries', [])),
                'user': info.get('uploader', get_text('ua', 'unknown_artist')),
            }
            
            return playlist_info
            
        except Exception:
            return None

    async def send_playlist_preview(self, message: types.Message, playlist_url: str, lang: str = "ua"):
        """Быстро отправляет превью и возвращает информацию для загрузки"""
        try:
            # получаю информацию о плейлисте
            playlist_info = await self.get_playlist_info(playlist_url)
            
            if not playlist_info:
                # заглушка если не получилось
                playlist_info = {
                    'title': get_text(lang, 'unknown_playlist'),
                    'track_count': 0,
                    'user': get_text(lang, 'unknown_artist')
                }
            
            # Очищаем название
            clean_title = self.clean_text(playlist_info['title'])
            clean_user = self.clean_text(playlist_info['user'])
            
            # Формируем подпись на ПРАВИЛЬНОМ языке
            caption = f"🎵 **{clean_title}**\n"
            caption += f"👤 **{get_text(lang, 'author')}:** {clean_user}\n"
            caption += f"📊 **{get_text(lang, 'track_count')}:** {playlist_info['track_count']}"
            
            # Если есть обложка - отправляем с обложкой
            if playlist_info.get('cover_url'):
                try:
                    response = requests.get(playlist_info['cover_url'], timeout=3)
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
                'title': clean_title,
                'user': clean_user,
                'track_count': playlist_info['track_count']
            }
            
        except Exception:
            # заглушка если не получилось полчить инфу
            return {
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

playlist_preview = PlaylistPreview()