import subprocess
import os
import shutil
import time
from config import CUGAN_CONFIG, TEMP_DIR

class UpscaleProcessor:
    def __init__(self, output_dir=None):
        self.exe_path = os.path.normpath(os.path.abspath(os.path.join("core", "bin", "realcugan", "realcugan-ncnn-vulkan.exe")))
        
        # Создаем подпапки для кадров внутри temp
        self.frames_in = os.path.join(TEMP_DIR, "frames_in")
        self.frames_out = os.path.join(TEMP_DIR, "frames_out")

        from config import OUTPUT_DIR
        self.output_dir = output_dir if output_dir else OUTPUT_DIR

    def _prepare_dirs(self):
        """Очистка и создание папок для кадров"""
        for d in [self.frames_in, self.frames_out]:
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)

    def process(self, input_path, output_filename="episode_4k_final.mp4"):
        input_path = os.path.normpath(os.path.abspath(input_path))
        output_path = os.path.normpath(os.path.abspath(os.path.join(self.output_dir, output_filename)))
        
        self._prepare_dirs()

        # --- ШАГ 1: Извлечение кадров ---
        print("[*] Шаг 3.1: Извлечение кадров из видео...")
        extract_cmd = [
            "ffmpeg", "-i", input_path,
            "-q:v", "2", # Высокое качество PNG
            os.path.join(self.frames_in, "frame_%06d.png")
        ]
        subprocess.run(extract_cmd, check=True, capture_output=True)

        # --- ШАГ 2: Апскейл папки ---
        print(f"[*] Шаг 3.2: Апскейл кадров через Real-CUGAN (GPU: {CUGAN_CONFIG['gpuid']})...")
        cugan_cmd = [
            self.exe_path,
            "-i", self.frames_in,
            "-o", self.frames_out,
            "-s", str(CUGAN_CONFIG["scale"]),
            "-n", str(CUGAN_CONFIG["noise"]),
            "-g", str(CUGAN_CONFIG["gpuid"])
        ]
        
        process = subprocess.Popen(cugan_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            if "%" in line:
                print(f"\r    Прогресс нейросети: {line.strip()}", end="")
        process.wait()
        print("\n[+] Кадры обработаны.")

        # --- ШАГ 3: Сборка видео с оригинальным звуком ---
        print("[*] Шаг 3.3: Сборка финального видео и перенос аудио...")
        # Мы берем кадры из frames_out, а звук из оригинального input_path
        assemble_cmd = [
            "ffmpeg", "-y",
            "-framerate", "23.976", # Стандарт для аниме, можно вытянуть динамически через ffprobe
            "-i", os.path.join(self.frames_out, "frame_%06d.png"),
            "-i", input_path, # Второй вход для звука
            "-map", "0:v",    # Берем видео из первого входа (кадры)
            "-map", "1:a?",   # Берем аудио из второго входа (если есть)
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",      # Высокое качество видео на выходе
            "-c:a", "copy",    # Копируем звук без перекодирования
            output_path
        ]
        
        subprocess.run(assemble_cmd, check=True, capture_output=True)
        
        # Очистка (по желанию можно закомментировать для отладки)
        # shutil.rmtree(self.frames_in)
        # shutil.rmtree(self.frames_out)
        
        print(f"[*] Финальный файл будет сохранен здесь: {output_path}")
        return output_path