import yt_dlp
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

class Downloader:
    def get_ydl_opts(self, output_dir):
        return {
            'outtmpl': os.path.join(output_dir, '%(title).80s.%(ext)s'),
            'format': 'bestaudio[ext=mp3]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'retries': 2,
        }
    
    async def download_playlist(self, url, output_dir, user_id=None, bot=None, lang="ua", total_tracks=0):
        logger.info(f"Начинаю загрузку: {url}")
        
        try:
            ydl_opts = self.get_ydl_opts(output_dir)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: yt_dlp.YoutubeDL(ydl_opts).download([url])
            )
            
            files = [f for f in os.listdir(output_dir) if f.endswith('.mp3')]
            success = len(files) > 0
            
            if success:
                logger.info(f"Успешно! Файлов: {len(files)}")
            else:
                logger.error("Не удалось скачать файлы")
                
            return success
            
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")
            return False

downloader = Downloader()