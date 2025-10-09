import yt_dlp
import os
import asyncio

async def download_playlist(url, output_dir):
    """Скачивает плейлист SoundCloud"""
    track_count = [0]  # счетчик в списке чтобы изменять в хуке
    
    def progress_hook(d):
        """Только готовые треки, без прогресса"""
        if d['status'] == 'finished':
            track_count[0] += 1
            filename = os.path.basename(d.get('filename', 'unknown'))
            name_only = os.path.splitext(filename)[0][:40]  # обрезаем длинные названия
            print(f"✅ {track_count[0]}. {name_only}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'no_progress': True,  # ВЫКЛЮЧАЕМ прогресс полностью
        'progress_hooks': [progress_hook],
    }
    
    try:
        loop = asyncio.get_event_loop()
        print(f"📥 Скачиваю плейлист...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Сначала получаем информацию о плейлисте чтобы узнать количество треков
            info = await loop.run_in_executor(None, ydl.extract_info, url, False)
            total_tracks = len(info.get('entries', []))
            print(f"🎵 Всего треков: {total_tracks}")
            
            # Затем скачиваем
            await loop.run_in_executor(None, ydl.download, [url])
        
        print(f"✅ Плейлист скачан! ({track_count[0]}/{total_tracks} треков)")
        return True
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        return False

class Downloader:
    def download_playlist(self, url, output_dir):
        return download_playlist(url, output_dir)

downloader = Downloader()