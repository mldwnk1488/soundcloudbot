import yt_dlp
import re
from aiogram import types
from io import BytesIO
import requests
import asyncio
import logging
from lang_bot.translations import get_text

logger = logging.getLogger(__name__)

class PlaylistPreview:
    def get_ydl_opts(self):
        return {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'ignoreerrors': True,
            'retries': 2,
        }
    
    async def get_content_info(self, url, message=None, lang="ua"):
        try:
            if message:
                loading_msg = await message.answer(get_text(lang, "getting_info"))
            
            db = self.get_db()
            if db:
                cached_playlist, cached_tracks = await db.get_cached_playlist(url)
                if cached_playlist:
                    if loading_msg:
                        try:
                            await loading_msg.delete()
                        except:
                            pass
                    return cached_playlist
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None, 
                lambda: yt_dlp.YoutubeDL(self.get_ydl_opts()).extract_info(url, download=False)
            )
            
            if not info:
                return {
                    'type': 'error',
                    'title': get_text(lang, 'unknown_playlist'),
                    'track_count': 0,
                    'user': get_text(lang, 'unknown_artist'),
                }
            
            content_type = "track"
            track_count = 1
            
            if info.get('_type') == 'playlist':
                content_type = "playlist"
                entries = info.get('entries', [])
                if isinstance(entries, list):
                    track_count = len(entries)
                else:
                    track_count = info.get('playlist_count', 1)
            elif 'entries' in info and isinstance(info['entries'], list):
                if len(info['entries']) > 1:
                    content_type = "playlist"
                    track_count = len(info['entries'])
            
            cover_url = info.get('thumbnail', '')
            
            raw_title = info.get('title', '')
            clean_title = self.clean_filename(raw_title, lang) or get_text(lang, 'unknown_playlist')
            
            user = info.get('uploader') or info.get('channel') or get_text(lang, 'unknown_artist')
            
            content_info = {
                'type': content_type,
                'title': clean_title,
                'cover_url': cover_url,
                'track_count': track_count,
                'user': user,
                'url': url,
            }
            
            if db:
                tracks_data = []
                if content_type == "playlist" and info.get('entries'):
                    tracks_data = [{'title': track.get('title', f'Track {i+1}')} for i, track in enumerate(info.get('entries', []))]
                else:
                    tracks_data = [{'title': info.get('title', 'Unknown Track')}]
                
                await db.cache_playlist(url, content_info, tracks_data)
            
            return content_info
            
        except Exception as e:
            logger.error(f"Ошибка получения информации: {e}")
            return {
                'type': 'error',
                'title': get_text(lang, 'unknown_playlist'),
                'track_count': 0,
                'user': get_text(lang, 'unknown_artist'),
                'error': str(e)
            }
        finally:
            if 'loading_msg' in locals():
                try:
                    await loading_msg.delete()
                except:
                    pass

    def clean_filename(self, filename, lang="ua"):
        if not filename:
            return get_text(lang, 'unknown')
        
        cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
        cleaned = cleaned.strip()
        
        if len(cleaned) > 50:
            cleaned = cleaned[:47] + "..."
        
        return cleaned if cleaned else get_text(lang, 'unknown')
    
    def set_db(self, db_instance):
        self.db = db_instance
    
    def get_db(self):
        return getattr(self, 'db', None)

playlist_preview = PlaylistPreview()