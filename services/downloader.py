import yt_dlp
import os
import asyncio
import re

def clean_filename(filename):
    cleaned = re.sub(r'\s*-\s*\d+:\d+:\d+', '', filename)
    cleaned = re.sub(r'\s*\d+\.\d+\s*[AP]M', '', cleaned)  
    cleaned = re.sub(r'\s*\d{1,2}:\d{2}\s*', '', cleaned)
    cleaned = re.sub(r'\s*[\d\.]+\s*[M]B', '', cleaned)
    cleaned = re.sub(r'[<>:"/\\|?*]', '', cleaned)
    return cleaned.strip() or 'track'

def is_youtube_url(url):
    return any(domain in url for domain in ['youtube.com', 'youtu.be', 'music.youtube.com'])

def is_soundcloud_url(url):
    return 'soundcloud.com' in url

async def download_playlist(url, output_dir):
    track_count = [0]
    
    def progress_hook(d):
        if d['status'] == 'finished':
            track_count[0] += 1
            filename = os.path.basename(d.get('filename', 'unknown'))
            name_only = clean_filename(os.path.splitext(filename)[0])[:40]
            print(f"✅ {track_count[0]}. {name_only}")

    # 🔥 ПРОСТЫЕ И РАБОЧИЕ НАСТРОЙКИ
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,  # 🔥 ВКЛЮЧАЕМ ЛОГИ ДЛЯ ДЕБАГА
        'no_warnings': False,
        'ignoreerrors': True,  # 🔥 ИГНОРИРУЕМ ОШИБКИ
        'extract_flat': False,
    }
    
    if is_youtube_url(url):
        ydl_opts.update({
            'format': 'bestaudio/best',
            # 🔥 МИНИМАЛЬНЫЕ НАСТРОЙКИ ДЛЯ YOUTUBE
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3', 
                'preferredquality': '192',
            }],
        })
    
    elif is_soundcloud_url(url):
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
        print(f"🔄 Начинаю скачивание: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await loop.run_in_executor(None, ydl.download, [url])
        
        # 🔥 ПРОВЕРЯЕМ РЕЗУЛЬТАТ
        files = [f for f in os.listdir(output_dir) if f.endswith(('.mp3', '.m4a', '.webm'))]
        print(f"📁 Скачано файлов: {len(files)}")
        
        return len(files) > 0  # Успех если есть хоть один файл
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

class Downloader:
    def download_playlist(self, url, output_dir):
        return download_playlist(url, output_dir)

downloader = Downloader()