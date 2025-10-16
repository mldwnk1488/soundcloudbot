import yt_dlp
import asyncio
import logging
import hashlib
import re

logger = logging.getLogger(__name__)

class ImprovedSoundCloudSearch:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'ignoreerrors': True,
        }
    
    async def search_tracks(self, query, limit=30):  # Увеличили лимит до 30
        """Улучшенный поиск треков"""
        try:
            logger.info(f"🔍 Поиск: {query} (лимит: {limit})")
            
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
                    track = self._improved_parse_track_info(entry)
                    if track:
                        tracks.append(track)
            
            logger.info(f"✅ Найдено треков: {len(tracks)}")
            return tracks
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    def _improved_parse_track_info(self, entry, lang="ru"):
    """Улучшенный парсинг информации о треке с учетом языка"""
    try:
        from lang_bot.translations import get_text
        
        track_url = entry.get('webpage_url', '')
        track_id = hashlib.md5(track_url.encode()).hexdigest() if track_url else str(entry.get('id', ''))
        
        # Улучшенное извлечение артиста и названия
        title = entry.get('title', get_text(lang, 'unknown')).strip()
        uploader = entry.get('uploader', get_text(lang, 'unknown_artist')).strip()
        
        # Пытаемся извлечь артиста из названия
        artist, clean_title = self._extract_artist_from_title(title, uploader, lang)
        
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
            'title': clean_title,
            'artist': artist,
            'duration': duration_ms,
            'permalink_url': track_url,
            'artwork_url': entry.get('thumbnail'),
            'streamable': True,
            'duration_formatted': duration_formatted,
            'original_title': title
        }
        
        return track
        
    except Exception as e:
        logger.error(f"❌ Error parsing track: {e}")
        return None

def _extract_artist_from_title(self, title, uploader, lang="ru"):
    """Извлекает артиста из названия трека с учетом языка"""
    from lang_bot.translations import get_text
    
    # Паттерны для извлечения артиста
    patterns = [
        r'^(.*?)\s*[-–—]\s*(.*)$',  # "Artist - Title"
        r'^(.*?)\s*[|]\s*(.*)$',    # "Artist | Title"
        r'^(.*?)\s*:\s*(.*)$',      # "Artist: Title"
        r'^(.*?)\s*«(.*)»$',        # "Artist «Title»"
        r'^(.*?)\s*"(.*)"$',        # 'Artist "Title"'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, title)
        if match:
            artist = match.group(1).strip()
            clean_title = match.group(2).strip()
            
            # Проверяем что артист не слишком длинный
            if len(artist) < 50 and len(clean_title) > 3:
                return artist, clean_title
    
    # Если не нашли паттерн, используем uploader как артиста
    if uploader and uploader != get_text(lang, 'unknown_artist'):
        return uploader, title
    else:
        return self._fallback_artist_extraction(title, lang)

def _fallback_artist_extraction(self, title, lang="ru"):
    """Альтернативные методы извлечения артиста"""
    from lang_bot.translations import get_text
    
    # Если в названии есть запятая, возможно это "Artist, Title"
    if ',' in title:
        parts = title.split(',', 1)
        if len(parts[0]) < 30:
            return parts[0].strip(), parts[1].strip()
    
    # Если название очень длинное, берем первую часть
    if len(title) > 40:
        for separator in [' - ', ' | ', ' : ']:
            if separator in title[:30]:
                parts = title.split(separator, 1)
                return parts[0].strip(), parts[1].strip()
    
    # Если ничего не помогло, возвращаем Unknown Artist на нужном языке
    return get_text(lang, "unknown_artist"), title
    
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
            
            track = self._improved_parse_track_info(info)
            if track:
                logger.info(f"✅ Информация получена: {track['title']} - {track['artist']}")
            return track
            
        except Exception as e:
            logger.error(f"❌ Get track info error: {e}")
            return None

# Заменяем старый поиск на улучшенный
search_engine = ImprovedSoundCloudSearch()