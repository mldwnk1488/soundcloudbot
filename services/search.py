import aiohttp
import asyncio
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

class SoundCloudSearch:
    def __init__(self):
        self.base_url = "https://api-v2.soundcloud.com"
        self.client_id = "a3e059563d7fd3372b49b37f00a00bcf"  # Public SoundCloud client_id
    
    async def search_tracks(self, query, limit=10):
        """Поиск треков на SoundCloud"""
        try:
            encoded_query = quote(query)
            url = f"{self.base_url}/search/tracks?q={encoded_query}&client_id={self.client_id}&limit={limit}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_search_results(data)
                    else:
                        logger.error(f"SoundCloud API error: {response.status}")
                        return []
        except asyncio.TimeoutError:
            logger.error("SoundCloud search timeout")
            return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _parse_search_results(self, data):
        """Парсинг результатов поиска"""
        tracks = []
        
        for item in data.get('collection', []):
            try:
                # Проверяем что трек доступен для прослушивания
                if item.get('policy') != 'ALLOW' or not item.get('streamable'):
                    continue
                
                track = {
                    'id': item.get('id'),
                    'title': item.get('title', 'Unknown Track'),
                    'artist': item.get('user', {}).get('username', 'Unknown Artist'),
                    'duration': item.get('duration', 0),
                    'permalink_url': item.get('permalink_url'),
                    'artwork_url': item.get('artwork_url'),
                    'streamable': item.get('streamable', False)
                }
                
                # Форматируем длительность
                if track['duration']:
                    minutes = track['duration'] // 60000
                    seconds = (track['duration'] % 60000) // 1000
                    track['duration_formatted'] = f"{minutes}:{seconds:02d}"
                else:
                    track['duration_formatted'] = "0:00"
                
                tracks.append(track)
            except Exception as e:
                logger.error(f"Error parsing track: {e}")
                continue
        
        return tracks
    
    async def get_track_info(self, track_url):
        """Получение информации о конкретном треке"""
        try:
            url = f"{self.base_url}/resolve?url={track_url}&client_id={self.client_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_track_info(data)
                    else:
                        logger.error(f"SoundCloud resolve error: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Get track info error: {e}")
            return None
    
    def _parse_track_info(self, data):
        """Парсинг информации о треке"""
        try:
            track = {
                'id': data.get('id'),
                'title': data.get('title', 'Unknown Track'),
                'artist': data.get('user', {}).get('username', 'Unknown Artist'),
                'duration': data.get('duration', 0),
                'permalink_url': data.get('permalink_url'),
                'artwork_url': data.get('artwork_url'),
                'streamable': data.get('streamable', False)
            }
            
            if track['duration']:
                minutes = track['duration'] // 60000
                seconds = (track['duration'] % 60000) // 1000
                track['duration_formatted'] = f"{minutes}:{seconds:02d}"
            else:
                track['duration_formatted'] = "0:00"
            
            return track
        except Exception as e:
            logger.error(f"Error parsing track info: {e}")
            return None

search_engine = SoundCloudSearch()