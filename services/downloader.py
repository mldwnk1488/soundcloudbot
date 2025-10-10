import yt_dlp
import os
import asyncio
import re

def clean_filename(filename):
    """Чистит название от хуйни"""
    cleaned = re.sub(r'\s*-\s*\d+:\d+:\d+', '', filename)  # " - 5:27:16"
    cleaned = re.sub(r'\s*\d+\.\d+\s*[AP]M', '', cleaned)  # "9.24 PM"  
    cleaned = re.sub(r'\s*\d{1,2}:\d{2}\s*', '', cleaned)  # "02:50"
    cleaned = re.sub(r'\s*[\d\.]+\s*[M]B', '', cleaned)    # "3.8 MB"
    cleaned = re.sub(r'[<>:"/\\|?*]', '', cleaned)
    return cleaned.strip() or 'track'

def is_youtube_url(url):
    """Проверяем YouTube URL"""
    return any(domain in url for domain in ['youtube.com', 'youtu.be', 'music.youtube.com'])

def is_soundcloud_url(url):
    """Проверяем SoundCloud URL"""
    return 'soundcloud.com' in url

async def download_playlist(url, output_dir):
    """Скачивает плейлист SoundCloud или YouTube"""
    track_count = [0]  # счетчик в списке чтобы изменять в хуке
    
    def progress_hook(d):
        """Только готовые треки, без прогресса"""
        if d['status'] == 'finished':
            track_count[0] += 1
            filename = os.path.basename(d.get('filename', 'unknown'))
            name_only = clean_filename(os.path.splitext(filename)[0])[:40]  # ЧИСТИМ НАЗВАНИЕ!
            print(f"✅ {track_count[0]}. {name_only}")

    # БАЗОВЫЕ НАСТРОЙКИ
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'no_progress': True,
        'progress_hooks': [progress_hook],
    }
    
    # НАСТРОЙКИ ДЛЯ YOUTUBE - БЫСТРЫЕ
    if is_youtube_url(url):  # <-- ДОБАВЬ ОТСТУП!
        ydl_opts.update({
            'format': 'bestaudio/best',
        # УСКОРЕННЫЕ НАСТРОЙКИ
            'concurrent_fragment_downloads': 8,
            'http_chunk_size': 2097152,
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'ignoreerrors': True,
            'noplaylist': False,
            'extractflat': True,
            'age_limit': 0,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3', 
                'preferredquality': '128',
            }],
        })
    # НАСТРОЙКИ ДЛЯ SOUNDCLOUD
    elif is_soundcloud_url(url):  # <-- ДОБАВЬ ОТСТУП!
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    
    try:
        loop = asyncio.get_event_loop()
        print(f"📥 Скачиваю плейлист: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Сначала получаем информацию о плейлисте
            info = await loop.run_in_executor(None, ydl.extract_info, url, False)
            total_tracks = len(info.get('entries', []))
            print(f"🎵 Всего треков: {total_tracks}")
            
            # Затем скачиваем
            await loop.run_in_executor(None, ydl.download, [url])
        
        print(f"✅ Плейлист скачан! ({track_count[0]}/{total_tracks} треков)")
        return True
    except Exception as e:
        print(f"❌ Ошибка скачивания {url}: {e}")
        return False

class Downloader:
    def download_playlist(self, url, output_dir):
        return download_playlist(url, output_dir)

downloader = Downloader()