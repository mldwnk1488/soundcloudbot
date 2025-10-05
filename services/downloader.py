import os
import asyncio
import yt_dlp
import re
from typing import Optional

def progress_hook(d):
    if d['status'] == 'downloading':
        print(f"скачивание: {d.get('_percent_str', '')} {d.get('filename', '')}")
    elif d['status'] == 'finished':
        print(f"закончил: {d.get('filename', '')}")

class PlaylistDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
            'noplaylist': False,
            'ignoreerrors': True,
            'progress_hooks': [progress_hook]
        }

    def get_playlist_title(self, url: str) -> str:


        """Получаю название плейлиста"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                playlist_title = info.get('title', 'playlist')
                
                # Очищаю название от недопустимых символов
                clean_title = re.sub(r'[<>:"/\\|?*]', '', playlist_title)
                clean_title = clean_title.replace(' ', '_')
                
                # Обрезаю слишком длинные названия
                if len(clean_title) > 50:
                    clean_title = clean_title[:50]
                
                return clean_title if clean_title else "playlist"
        except Exception as e:
            print(f"ошибка получения названия плейлиста: {e}")
            return "playlist"

    async def download_playlist(self, url: str, download_path: str):
        """Скачиваю плейлист"""
        self.ydl_opts['outtmpl'] = os.path.join(download_path, '%(title)s.%(ext)s')
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: yt_dlp.YoutubeDL(self.ydl_opts).download([url])
        )



downloader = PlaylistDownloader()