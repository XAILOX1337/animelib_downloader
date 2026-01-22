from playwright.sync_api import sync_playwright
import time
import os
from config import HEADERS




class AnimeScraper:
    def __init__(self):
        self.video_url = None
        self.video_type = None
        # Путь к распакованному AdBlock 
        self.extension_path = os.path.abspath("core/extensions/adblock")

    def _intercept_network(self, request):
        url = request.url
        if ".mp4" in url and ("_1080" in url or "_2160" in url):
            self.video_url = url
            self.video_type = "mp4"
        elif ".m3u8" in url and "720" in url:
            # Проверяем, что это не мелкое разрешение (ищем упоминание 1080 в URL m3u8 если есть)
            self.video_url = url
            self.video_type = "m3u8"

    def get_video_link(self, page_url):
        
        with sync_playwright() as p:
            
            # Запуск с поддержкой расширений 
            user_data_dir = os.path.abspath("data/browser_profile")
            
            # Если папка расширения есть — используем, если нет — просто запускаем
            args = []
            if os.path.exists(self.extension_path):
                args = [
                    f"--disable-extensions-except={self.extension_path}",
                    f"--load-extension={self.extension_path}",
                ]

            context = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False, # Расширения работают только в видимом режиме
                args=args,
                user_agent=HEADERS["User-Agent"],
                viewport={'width': 1280, 'height': 720}
            )
            
            page = context.new_page()
            page.on("request", self._intercept_network)

            print(f"[*] Переход на: {page_url}")
            page.goto(page_url, wait_until="domcontentloaded")
            
            try:
                page.wait_for_timeout(500)
                # 1. Кликаем Play
                if self.video_type == "mp4":
                    
                    print("[*] Пытаюсь запустить плеер...", flush=True)
                    page.wait_for_selector(".svg-inline--fa.fa-play > path", timeout=10000)
                    page.locator(".svg-inline--fa.fa-play > path").first.click()
                    
                    # 2. Выбор качества 1080p
                    page.wait_for_timeout(2000)
                    
                    # Ищем кнопку качества 
                    print("[*] Выбираю наилучшее качество...", flush=True)
                    
                    page.locator("div:nth-child(6)").first.click()
                    q_2160 = page.get_by_text("2160p", exact=False)
                    q_1080 = page.get_by_text("1080p", exact=False)

                    
                    
                    page.get_by_text("Качество").click()
                    
                    page.wait_for_timeout(500)
                    if q_2160.is_visible():
                        print("[*] Найдено разрешение 2160p. Выбираю...", flush=True)
                        q_2160.click()
                    elif q_1080.is_visible():
                        print("[*] 2160p не найдено. Выбираю 1080p...", flush=True)
                        q_1080.click()
                elif self.video_type == "m3u8":
                    print("--- DEBUG:--")
                    page.click("play_button")
                    page.locator("iframe").content_frame.locator("a").click()
                    page.locator("iframe").content_frame.get_by_role("cell", name="360p").locator("span").click()
                    page.locator("iframe").content_frame.get_by_text("720p").click()
                


                
                # 3. Ждем поимки ссылки в сетевом трафике
                timeout = 30
                start_time = time.time()
                while not self.video_url and (time.time() - start_time < timeout):
                    page.wait_for_timeout(500)

            except Exception as e:
                print(f"[!] Ошибка при автоматизации действий: {e}")
            
            context.close()
            
            if not self.video_url:
                raise Exception("[-] Не удалось поймать ссылку автоматически.")
            
            return self.video_url, self.video_type