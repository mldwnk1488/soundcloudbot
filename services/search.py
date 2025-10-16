import yt_dlp
import asyncio
import logging
import hashlib

logger = logging.getLogger(__name__)

class SoundCloudSearch:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'ignoreerrors': True,
        }
    
    async def search_tracks(self, query, limit=10):
        """Поиск треков через yt-dlp"""
        try:
            logger.info(f"🔍 Поиск: {query}")
            
            search_url = f"scsearch{limit}:{query}"
            
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None, 
                    lambda: ydl.extract_info(search_url, download=False)
                )
            
            if not info or 'entries' not in info:
                logger.error("❌ Не удалось получить результаты поиска")
                return []
            
            tracks = []
            for entry in info['entries']:
                if entry:
                    track = self._parse_track_info(entry)
                    if track:
                        tracks.append(track)
                        logger.info(f"✅ Трек: {track['title']}")
            
            logger.info(f"✅ Найдено треков: {len(tracks)}")
            return tracks[:limit]
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    def _parse_track_info(self, entry):
        """Парсинг информации о треке"""
        try:
            # Создаем стабильный ID из URL
            track_url = entry.get('webpage_url', '')
            track_id = hashlib.md5(track_url.encode()).hexdigest() if track_url else str(entry.get('id', ''))
            
            # Безопасно получаем длительность
            duration = entry.get('duration', 0)
            if isinstance(duration, (int, float)) and duration > 0:
                duration_ms = int(duration * 1000)
                minutes = duration_ms // 60000
                seconds = (duration_ms % 60000) // 1000
                duration_formatted = f"{minutes}:{seconds:02d}"
            else:
                duration_ms = 0
                duration_formatted = "0:00"
            
            track = {
                'id': track_id,
                'title': entry.get('title', 'Unknown Track').strip(),
                'artist': entry.get('uploader', 'Unknown Artist').strip(),
                'duration': duration_ms,
                'permalink_url': track_url,
                'artwork_url': entry.get('thumbnail'),
                'streamable': True,
                'duration_formatted': duration_formatted
            }
            
            logger.debug(f"🎵 Парсинг трека: {track['title']} - {track['artist']}")
            return track
            
        except Exception as e:
            logger.error(f"❌ Error parsing track: {e}")
            logger.error(f"❌ Entry data: {entry}")
            return None
    
    async def get_track_info(self, track_url):
        """Получение информации о конкретном треке"""
        try:
            logger.info(f"🔍 Получение информации о треке: {track_url}")
            
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None, 
                    lambda: ydl.extract_info(track_url, download=False)
                )
            
            if not info:
                logger.error("❌ Не удалось получить информацию о треке")
                return None
            
            track = self._parse_track_info(info)
            if track:
                logger.info(f"✅ Информация получена: {track['title']}")
            return track
            
        except Exception as e:
            logger.error(f"❌ Get track info error: {e}")
            return None

search_engine = SoundCloudSearch()