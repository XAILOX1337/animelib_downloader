import sys
import os
from core.scraper import AnimeScraper
from core.downloader import VideoDownloader
from core.upscale import UpscaleProcessor

def start_pipeline(anime_url):
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
        raw_video_path = downloader.download(video_url, video_type, "episode_raw.mp4")
        
        # ЭТАП 3: Апскейл через бинарник Real-CUGAN
        # print("\n[3/3] Запуск нейросетевой обработки (Real-CUGAN)...")
        # processor = UpscaleProcessor()
        # # Итоговый файл попадет в папку data/output
        # final_video_path = processor.process(raw_video_path, "episode_4k_final.mp4")

        # print("\n" + "="*50)
        # print(f"ПОЛНЫЙ ЦИКЛ ЗАВЕРШЕН!")
        # print(f"Результат: {final_video_path}")
        # print("="*50)

       
        # os.remove(raw_video_path)

    except Exception as e:
        print(f"\n[КРИТИЧЕСКАЯ ОШИБКА] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    
    TARGET_URL = input("Введите ссылку: ")
    
    start_pipeline(TARGET_URL)