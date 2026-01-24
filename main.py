import sys
import os
from core.scraper import AnimeScraper
from core.downloader import VideoDownloader
from core.upscale import UpscaleProcessor
from config import OUTPUT_DIR, TEMP_DIR

def get_user_settings():
    print("\n=== Настройка путей ===")
    
    # Запрос пути сохранения
    default_path = os.path.abspath(OUTPUT_DIR)
    user_input = input(f"Введите путь для сохранения (Enter для использования '{default_path}'): ").strip()
    
    # Если пользователь ничего не ввел, используем стандартный путь
    if not user_input:
        final_output_dir = default_path
    else:
        final_output_dir = os.path.abspath(user_input)
    
    # Создаем папку, если её нет
    if not os.path.exists(final_output_dir):
        try:
            os.makedirs(final_output_dir)
            print(f"[+] Создана новая папка: {final_output_dir}")
        except Exception as e:
            print(f"[!] Ошибка создания папки: {e}. Использую путь по умолчанию.")
            final_output_dir = default_path
            
    return final_output_dir


def start_pipeline(TARGET_URL, custom_output_path):
    """
    Основной конвейер: Поиск ссылки -> Скачивание -> Апскейл
    """
    print("\n" + "="*50)
    print("      ANIME UPSCALER PIPELINE STARTING")
    print("="*50 + "\n")
    
    try:
        # ЭТАП 1: Поиск прямой ссылки через Playwright
        print("[1/3] Поиск прямой ссылки на видео...")
        scraper = AnimeScraper()
        # Передаем URL страницы, scraper вернет прямую ссылку на .mp4
        video_url, video_type = scraper.get_video_link(TARGET_URL)
        print(f"[УСПЕХ] Ссылка получена.")

        # ЭТАП 2: Скачивание через FFmpeg
        print("\n[2/3] Запуск загрузки видео...")
        downloader = VideoDownloader()
        # Сохраняем во временную папку под коротким именем
        downloader.download(video_url, video_type, "episode_raw.mp4")
        
        # ЭТАП 3: Апскейл через бинарник Real-CUGAN
        print("\n[3/3] Запуск нейросетевой обработки (Real-CUGAN)...")
        processor = UpscaleProcessor(custom_output_path)
        
        processor.process(TEMP_DIR + "/episode_raw.mp4", "episode_4k_final.mp4")

        print("\n" + "="*50)
        print(f"ПОЛНЫЙ ЦИКЛ ЗАВЕРШЕН!")
        print(f"Результат: {custom_output_path}")
        print("="*50)

       
        # os.remove(raw_video_path)

    except Exception as e:
        print(f"\n[КРИТИЧЕСКАЯ ОШИБКА] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    custom_output_dir = get_user_settings()
    TARGET_URL = input("Введите ссылку: ")
    
    start_pipeline(TARGET_URL, custom_output_dir)