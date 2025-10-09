import zipfile
import os
import math

def create_zip(source_dir, zip_path):
    """Создает ZIP архив из директории"""
    try:
        print(f"📦 Создаю ZIP из {source_dir} в {zip_path}")
        file_count = 0
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
                    file_count += 1
                    print(f"📄 Добавлен файл в ZIP: {file}")
        
        print(f"✅ ZIP создан успешно: {zip_path}, файлов: {file_count}")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания ZIP: {e}")
        return False

def get_files_in_directory(directory):
    """Получает список файлов в директории"""
    files = []
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                files.append(item)
        print(f"📁 Найдено файлов в {directory}: {len(files)}")
    except Exception as e:
        print(f"❌ Ошибка чтения директории: {e}")
    return files

def create_zip_parts(source_dir, zip_base_path, max_part_size=45*1024*1024):
    """Создает ZIP архив, разбитый на части"""
    try:
        print(f"📦 Создаю части архива из {source_dir}")
        
        part_num = 1
        current_part_size = 0
        current_zip = None
        zip_parts = []
        
        # Собираем все файлы
        all_files = []
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append((file, file_path))
        
        # Сортируем файлы по размеру (оптимально для упаковки)
        all_files.sort(key=lambda x: os.path.getsize(x[1]))
        
        for file_name, file_path in all_files:
            file_size = os.path.getsize(file_path)
            
            # Если файл сам по себе больше максимального размера части
            if file_size > max_part_size:
                print(f"⚠️ Файл {file_name} слишком большой ({file_size/1024/1024:.1f}MB), пропускаем")
                continue
            
            # Если нужно начать новую часть
            if current_zip is None or current_part_size + file_size > max_part_size:
                if current_zip is not None:
                    current_zip.close()
                    print(f"✅ Часть {part_num} создана: {current_zip_path} ({current_part_size/1024/1024:.1f}MB)")
                
                # Создаем новую часть
                current_zip_path = f"{zip_base_path}.part{part_num:03d}.zip"
                current_zip = zipfile.ZipFile(current_zip_path, 'w', zipfile.ZIP_DEFLATED)
                zip_parts.append(current_zip_path)
                current_part_size = 0
                part_num += 1
            
            # Добавляем файл в текущую часть
            arcname = file_name
            current_zip.write(file_path, arcname)
            current_part_size += file_size
            print(f"📄 Добавлен в часть {part_num-1}: {file_name}")
        
        # Закрываем последнюю часть
        if current_zip is not None:
            current_zip.close()
            print(f"✅ Часть {part_num-1} создана: {current_zip_path} ({current_part_size/1024/1024:.1f}MB)")
        
        print(f"🎯 Создано частей: {len(zip_parts)}")
        return zip_parts
        
    except Exception as e:
        print(f"❌ Ошибка создания частей архива: {e}")
        return []

# 🔥 ОБНОВЛЕННЫЙ КЛАСС:
class FileProcessor:
    def create_zip(self, source_dir, zip_path):
        return create_zip(source_dir, zip_path)
    
    def get_files_in_directory(self, directory):
        return get_files_in_directory(directory)
    
    def create_zip_parts(self, source_dir, zip_base_path, max_part_size=45*1024*1024):
        return create_zip_parts(source_dir, zip_base_path, max_part_size)

file_processor = FileProcessor()