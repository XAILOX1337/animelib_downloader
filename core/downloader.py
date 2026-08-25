import os
import subprocess
import re

from config import HEADERS, TEMP_DIR


class VideoDownloader:
    def __init__(self):
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("[-] FFmpeg не найден. Установите его и добавьте в PATH.")

    def download(self, url, file_type, filename="episode_raw.mp4"):
        output_path = os.path.join(TEMP_DIR, filename)
        headers_str = "".join([f"{k}: {v}\r\n" for k, v in HEADERS.items()])

        command = [
            "ffmpeg", "-y",
            "-headers", headers_str,
            "-timeout", "10000000",
            "-rw_timeout", "10000000",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
        ]

        if file_type == "m3u8":
            command += [
                "-protocol_whitelist", "file,http,https,tcp,tls,crypto,httpls,concat",
                "-max_reload", "10",
            ]

        command += [
            "-i", url,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            output_path
        ]

        print(f"[*] Загрузка пошла ({file_type})...")
        print(f"[*] Сохраняю как: {filename}")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        for line in process.stdout:
            line = line.rstrip()
            if line:
                if "time=" in line or "speed=" in line:
                    time_match = re.search(r"time=(\S+)", line)
                    speed_match = re.search(r"speed=(\S+)", line)
                    if time_match or speed_match:
                        t = time_match.group(1) if time_match else "?"
                        s = speed_match.group(1) if speed_match else "?"
                        print(f"\r    [загрузка] time={t}  speed={s}        ", end="", flush=True)
                elif "error" in line.lower() or "failed" in line.lower():
                    print(f"\n    [!] {line}")

        process.wait()
        print()

        if process.returncode != 0:
            raise Exception(f"FFmpeg не смог скачать поток (код {process.returncode}).")

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 1024:
            raise Exception("Файл пустой или повреждён после загрузки.")

        file_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[+] Загрузка завершена: {filename} ({file_mb:.1f} MB)")
        return output_path