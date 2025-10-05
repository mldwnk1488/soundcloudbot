import os
import zipfile

class FileProcessor:
    @staticmethod
    def create_zip(src_dir: str, zip_path: str):
        """Создаю ZIP архив"""
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(src_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, src_dir)
                    zipf.write(file_path, arcname)

    @staticmethod
    def get_files_in_directory(directory: str):

        
        """Получаю список файлов в директории"""
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

file_processor = FileProcessor()