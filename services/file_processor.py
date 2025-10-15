import zipfile
import os
import math

def create_zip(source_dir, zip_path):
    """Создает ZIP архив из директории"""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 🔥 ИСПРАВЛЕНО: проверяем что файл существует и доступен
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
        return True
    except Exception as e:
        print(f"❌ Ошибка создания ZIP: {e}")
        return False

def get_files_in_directory(directory):
    """Получает список файлов в директории"""
    files = []
    try:
        # 🔥 ИСПРАВЛЕНО: проверяем что директория существует
        if not os.path.exists(directory):
            print(f"❌ Директория не существует: {directory}")
            return files
            
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                files.append(item)
    except Exception as e:
        print(f"❌ Ошибка чтения директории: {e}")
    return files

def create_zip_parts(source_dir, zip_base_path, max_part_size=45*1024*1024):
    """Создает ZIP архив, разбитый на части по 45MB"""
    current_zip = None
    zip_parts = []
    
    try:
        # 🔥 ИСПРАВЛЕНО: проверяем что исходная директория существует и не пуста
        if not os.path.exists(source_dir):
            print(f"❌ Исходная директория не существует: {source_dir}")
            return []
            
        # Собираем все файлы
        all_files = []
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    all_files.append((file, file_path))
        
        # 🔥 ИСПРАВЛЕНО: проверяем что есть файлы для архивации
        if not all_files:
            print("❌ Нет файлов для архивации")
            return []
        
        # Сортируем файлы по размеру (оптимально для упаковки)
        all_files.sort(key=lambda x: os.path.getsize(x[1]))
        
        part_num = 1
        current_part_size = 0
        
        for file_name, file_path in all_files:
            file_size = os.path.getsize(file_path)
            
            # 🔥 ИСПРАВЛЕНО: проверяем что можем прочитать файл
            if not os.access(file_path, os.R_OK):
                print(f"⚠️ Нет доступа к файлу: {file_name}")
                continue
            
            # Если файл сам по себе больше максимального размера части
            if file_size > max_part_size:
                print(f"⚠️ Файл {file_name} слишком большой ({file_size/1024/1024:.1f}MB), пропускаем")
                continue
            
            # Если нужно начать новую часть
            if current_zip is None or current_part_size + file_size > max_part_size:
                if current_zip is not None:
                    current_zip.close()
                    current_zip = None
                
                # Создаем новую часть
                current_zip_path = f"{zip_base_path}.part{part_num:03d}.zip"
                try:
                    # 🔥 ИСПРАВЛЕНО: используем with для автоматического закрытия
                    current_zip = zipfile.ZipFile(current_zip_path, 'w', zipfile.ZIP_DEFLATED)
                    zip_parts.append(current_zip_path)
                    current_part_size = 0
                    part_num += 1
                except Exception as e:
                    print(f"❌ Ошибка создания части архива {current_zip_path}: {e}")
                    continue
            
            # Добавляем файл в текущую часть
            try:
                arcname = file_name
                current_zip.write(file_path, arcname)
                current_part_size += file_size
            except Exception as e:
                print(f"❌ Ошибка добавления файла {file_name} в архив: {e}")
                continue
        
        return zip_parts
        
    except Exception as e:
        print(f"❌ Ошибка создания частей архива: {e}")
        return []
    finally:
        # 🔥 ИСПРАВЛЕНО: гарантированное закрытие ZIP файла
        if current_zip is not None:
            try:
                current_zip.close()
            except:
                pass

def cleanup_zip_parts(zip_parts):
    """Очищает временные ZIP части"""
    for part_path in zip_parts:
        try:
            if os.path.exists(part_path):
                os.remove(part_path)
                print(f"🧹 Удален временный файл: {part_path}")
        except Exception as e:
            print(f"⚠️ Не удалось удалить {part_path}: {e}")

class FileProcessor:
    def create_zip(self, source_dir, zip_path):
        return create_zip(source_dir, zip_path)
    
    def get_files_in_directory(self, directory):
        return get_files_in_directory(directory)
    
    def create_zip_parts(self, source_dir, zip_base_path, max_part_size=45*1024*1024):
        return create_zip_parts(source_dir, zip_base_path, max_part_size)
    
    def cleanup_zip_parts(self, zip_parts):
        """🔥 ДОБАВЛЕНО: метод для очистки временных файлов"""
        cleanup_zip_parts(zip_parts)

file_processor = FileProcessor()