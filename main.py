import sys
import os
import shutil
from core.scraper import AnimeScraper
from core.downloader import VideoDownloader
from core.upscale import UpscaleProcessor
from config import OUTPUT_DIR, TEMP_DIR


def get_user_settings():
    print("\n=== Настройка путей ===")

    default_path = os.path.abspath(OUTPUT_DIR)
    user_input = input(
        f"Введите путь для сохранения (Enter для использования '{default_path}'): "
    ).strip()

    if not user_input:
        final_output_dir = default_path
    else:
        final_output_dir = os.path.abspath(user_input)

    if not os.path.exists(final_output_dir):
        try:
            os.makedirs(final_output_dir)
            print(f"[+] Создана новая папка: {final_output_dir}")
        except Exception as e:
            print(f"[!] Ошибка создания папки: {e}. Использую путь по умолчанию.")
            final_output_dir = default_path

    return final_output_dir


def build_filename(title, episode_str, suffix="raw"):
    safe_name = title if title else "Unknown_anime"

    if episode_str == "Фильм":
        episode_part = "Фильм"
    else:
        episode_part = f"{episode_str} эпизод"

    return f"{safe_name} - {episode_part}_{suffix}.mp4"


def start_pipeline(TARGET_URL, custom_output_path):
    print("\n" + "=" * 50)
    print("      ANIME UPSCALER PIPELINE STARTING")
    print("=" * 50 + "\n")

    try:
        print("[1/3] Поиск прямой ссылки на видео...")
        scraper = AnimeScraper()
        video_url, video_type, title, episode_str = scraper.get_video_link(TARGET_URL)
        print(f"[УСПЕХ] Ссылка получена.")

        raw_filename = build_filename(title, episode_str, suffix="raw")
        final_filename = build_filename(title, episode_str, suffix="4k_final")
        raw_path = os.path.join(TEMP_DIR, raw_filename)

        print(f"\n[2/3] Запуск загрузки видео...")
        downloader = VideoDownloader()
        downloader.download(video_url, video_type, raw_filename)

        needUpscale = False
        usersChoose = input(
            "Хотите ли вы проапскейлить скачанное видео? (y/n) (По умолчанию n): "
        )
        if usersChoose == "y":
            needUpscale = True

        if needUpscale:
            print("\n[3/3] Запуск нейросетевой обработки (Real-CUGAN)...")
            processor = UpscaleProcessor(custom_output_path)
            processor.process(raw_path, final_filename)
        else:
            destination = os.path.join(custom_output_path, raw_filename)
            shutil.move(raw_path, destination)
            print(f"[*] Файл перемещён: {destination}")

        print("\n" + "=" * 50)
        print(f"Конец загрузки!")
        print(f"Результат: {custom_output_path}")
        print("=" * 50)

    except Exception as e:
        print(f"\n[КРИТИЧЕСКАЯ ОШИБКА] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    custom_output_dir = get_user_settings()
    TARGET_URL = input("Введите ссылку: ")
    start_pipeline(TARGET_URL, custom_output_dir)