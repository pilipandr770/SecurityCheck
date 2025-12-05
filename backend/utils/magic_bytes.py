"""
Словарь магических байт для определения типа файла
"""

# Магические байты (сигнатуры) файлов
MAGIC_SIGNATURES = {
    # Архивы
    b'\x50\x4B\x03\x04': 'zip',
    b'\x50\x4B\x05\x06': 'zip',
    b'\x50\x4B\x07\x08': 'zip',
    b'\x52\x61\x72\x21\x1A\x07': 'rar',
    b'\x1F\x8B\x08': 'gz',
    b'\x42\x5A\x68': 'bz2',
    b'\x75\x73\x74\x61\x72': 'tar',
    
    # Исполняемые файлы
    b'\x4D\x5A': 'exe',  # Windows executable
    b'\x7F\x45\x4C\x46': 'elf',  # Linux executable
    b'\x4D\x5A\x90': 'exe',
    
    # Документы
    b'\x25\x50\x44\x46': 'pdf',
    b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': 'doc/xls',  # MS Office старый
    b'\x50\x4B\x03\x04\x14\x00\x06\x00': 'docx/xlsx',  # MS Office новый
    
    # Изображения
    b'\xFF\xD8\xFF': 'jpg',
    b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A': 'png',
    b'\x47\x49\x46\x38\x37\x61': 'gif',  # GIF87a
    b'\x47\x49\x46\x38\x39\x61': 'gif',  # GIF89a
    b'\x42\x4D': 'bmp',
    b'\x49\x49\x2A\x00': 'tiff',  # TIFF little-endian
    b'\x4D\x4D\x00\x2A': 'tiff',  # TIFF big-endian
    
    # Видео
    b'\x00\x00\x00\x18\x66\x74\x79\x70': 'mp4',
    b'\x00\x00\x00\x20\x66\x74\x79\x70': 'mp4',
    b'\x1A\x45\xDF\xA3': 'mkv',
    b'\x52\x49\x46\x46': 'avi',  # Нужна доп. проверка
    
    # Аудио
    b'\x49\x44\x33': 'mp3',  # ID3 тег
    b'\xFF\xFB': 'mp3',
    b'\xFF\xF3': 'mp3',
    b'\xFF\xF2': 'mp3',
}


def get_file_signature(file_path, read_bytes=16):
    """
    Прочитать первые байты файла
    
    Args:
        file_path: Путь к файлу
        read_bytes: Количество байт для чтения
        
    Returns:
        bytes: Первые байты файла
    """
    try:
        with open(file_path, 'rb') as f:
            return f.read(read_bytes)
    except Exception:
        return b''


def detect_file_type(file_path):
    """
    Определить тип файла по магическим байтам
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        str: Тип файла или None
    """
    signature = get_file_signature(file_path)
    
    if not signature:
        return None
    
    # Проверяем каждую известную сигнатуру
    for magic_bytes, file_type in MAGIC_SIGNATURES.items():
        if signature.startswith(magic_bytes):
            return file_type
    
    # Дополнительные проверки для некоторых форматов
    
    # AVI (RIFF + AVI )
    if signature[:4] == b'\x52\x49\x46\x46' and signature[8:12] == b'AVI ':
        return 'avi'
    
    # WAV (RIFF + WAVE)
    if signature[:4] == b'\x52\x49\x46\x46' and signature[8:12] == b'WAVE':
        return 'wav'
    
    return None


def is_fake_extension(file_path, declared_extension):
    """
    Проверить подделано ли расширение файла
    
    Args:
        file_path: Путь к файлу
        declared_extension: Заявленное расширение (без точки)
        
    Returns:
        bool: True если расширение не соответствует содержимому
    """
    real_type = detect_file_type(file_path)
    
    if not real_type:
        return False  # Не можем определить
    
    # Нормализуем расширение
    declared = declared_extension.lower().strip('.')
    
    # Маппинг расширений к типам
    extension_map = {
        'zip': 'zip',
        'rar': 'rar',
        'gz': 'gz',
        'tar': 'tar',
        'bz2': 'bz2',
        'exe': 'exe',
        'dll': 'exe',
        'com': 'exe',
        'pdf': 'pdf',
        'doc': 'doc/xls',
        'xls': 'doc/xls',
        'docx': 'docx/xlsx',
        'xlsx': 'docx/xlsx',
        'jpg': 'jpg',
        'jpeg': 'jpg',
        'png': 'png',
        'gif': 'gif',
        'bmp': 'bmp',
        'mp4': 'mp4',
        'mp3': 'mp3',
        'avi': 'avi',
        'wav': 'wav',
        'mkv': 'mkv',
        'tiff': 'tiff',
        'tif': 'tiff'
    }
    
    expected_type = extension_map.get(declared)
    
    if not expected_type:
        return False  # Неизвестное расширение
    
    return real_type != expected_type


def get_magic_number(file_path, length=16):
    """
    Получить магическое число файла в hex формате
    
    Args:
        file_path: Путь к файлу
        length: Количество байт
        
    Returns:
        str: Hex представление
    """
    signature = get_file_signature(file_path, length)
    return signature.hex().upper()
