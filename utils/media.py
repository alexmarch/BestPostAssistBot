import os


def remove_media_file(file_path: str):
    """
    Удаляет медиафайл по указанному пути.
    :param file_path: Путь к файлу.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Файл {file_path} успешно удален.")
        else:
            print(f"Файл {file_path} не существует.")
    except Exception as e:
        print(f"Ошибка при удалении файла {file_path}: {e}")
