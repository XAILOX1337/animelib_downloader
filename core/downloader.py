import os
import subprocess

from config import HEADERS, TEMP_DIR


class VideoDownloader:
    def __init__(self):
        # Проверяем, установлен ли ffmpeg в системе
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("[-] FFmpeg не найден. Установите его и добавьте в PATH.")

    def download(self, url, filename="raw_video.mp4"):
        output_path = os.path.join(TEMP_DIR, filename)

        # Формируем строку заголовков для ffmpeg
        # Важно: ffmpeg принимает заголовки в одну строку, разделенную \r\n
        headers_str = "".join([f"{k}: {v}\r\n" for k, v in HEADERS.items()])

        print(f"[*] Начало загрузки видео в: {output_path}")

        # Формируем команду
        command = [
            "ffmpeg",
            "-y",  # Перезаписывать файл, если он существует
            "-headers",
            headers_str,
            "-i",
            url,  # Входной URL
            "-c",
            "copy",  # Копируем потоки без перекодирования (макс. скорость)
            "-bsf:a",
            "aac_adtstoasc",  # Исправление метаданных аудио для mp4
            output_path,
        ]

        try:
            # Запускаем процесс. stderr=subprocess.STDOUT позволит видеть прогресс ffmpeg
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print("[+] Загрузка успешно завершена.")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"[-] Ошибка FFmpeg: {e.stderr}")
            raise Exception("Не удалось скачать видео.")
