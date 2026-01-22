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

    def download(self, url, file_type, filename="episode_raw.mp4"):
        import subprocess
        from config import HEADERS, TEMP_DIR
        
        output_path = os.path.join(TEMP_DIR, filename)
        headers_str = "".join([f"{k}: {v}\r\n" for k, v in HEADERS.items()])

        # Базовая команда
        command = ["ffmpeg", "-y", "-headers", headers_str]

        # Если это плейлист, добавляем разрешения на чтение сетевых протоколов
        if file_type == "m3u8":
            command += ["-protocol_whitelist", "file,http,https,tcp,tls,crypto"]

        command += ["-i", url, "-c", "copy", "-bsf:a", "aac_adtstoasc", output_path]

        print(f"[*] Загрузка пошла ({file_type})...")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[-] Ошибка загрузки: {result.stderr}")
            raise Exception("FFmpeg не смог скачать поток.")
            
        return output_path
