from playwright.sync_api import sync_playwright
import time
import os
import re
from config import HEADERS

# рекламные домены 
AD_KEYWORDS = [
    # Рекламная хуйня Яндекса
    "strm.yandex.ru",        
    "an.yandex.ru",          
    "yandex.ru/clck",        
    "adfox.ru",              
    "adfox.yandex",          
    "yandexadexchange.net",  
    "awaps.yandex.net",     
    "mc.yandex.ru",        
    "yastatic.net/adv",    
    # # Прочие распространённые рекламные/аналитические сети
    # "googleads",
    # "doubleclick",
    # "googlesyndication",
    # "google-analytics",
    # "adservice",
    # "adsense",
    # "adsystem",
    # "taboola",
    # "outbrain",
    # "criteo",
    # "adsrvr",
    # "pubmatic",
    # "pixel",
]


class AnimeScraper:
    def __init__(self):
        self.video_url = None
        self.video_type = None
        self.title = None
        self.episode_str = None
        self.blocked_count = 0

        _file_dir = os.path.dirname(os.path.abspath(__file__))
        self.extension_path = os.path.normpath(
            os.path.join(_file_dir, "extensions", "uBlock")
        )
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    def _intercept_network(self, request):
        url = request.url
        if ".mp4" in url and ("_1080" in url or "_2160" in url or "_1004" in url):
            self.video_url = url
            self.video_type = "mp4"
        elif ".m3u8" in url and ("720" in url or "480" in url):
            self.video_url = url
            self.video_type = "m3u8"

    def _block_ads(self, route):
        """Блокировщик рекламы прерывает запросы с рекламными URL, описанными в AD_KEYWORDS."""
        try:
            url = route.request.url
            for keyword in AD_KEYWORDS:
                if keyword in url:
                    self.blocked_count += 1
                    print(f"Заблокировано ({keyword})")
                    route.abort()
                    return
            route.continue_()
        except Exception:
            # На всякий
            pass

    @staticmethod
    def _sanitize_filename(name):
        """Функция для удаления запрещенных символов из названия файла"""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '')
        return name.strip('. ')

    def _extract_title(self, page):
        """Функция для извлечения названия тайтла"""
        try:
            title_el = page.locator("h1 a").first
            title_el.wait_for(state="visible", timeout=5000)
            raw_title = title_el.inner_text().strip()
            if raw_title:
                return self._sanitize_filename(raw_title)
        except Exception:
            pass

        try:
            og_title = page.locator('meta[property="og:title"]').get_attribute("content")
            if og_title:
                return self._sanitize_filename(og_title.strip())
        except Exception:
            pass

        try:
            page_title = page.title()
            if page_title:
                for suffix in [" — Анимелиб", " | Анимелиб", " — смотреть онлайн",
                               " онлайн", " — AnimeLib", " | AnimeLib"]:
                    page_title = page_title.replace(suffix, "")
                cleaned = self._sanitize_filename(page_title.strip())
                if cleaned:
                    return cleaned
        except Exception:
            pass

        return None

    def _extract_episode_info(self, page, page_url):
        try:
            page.wait_for_selector("div[id^='episode_']", timeout=10000)
        except Exception:
            pass

        url_match = re.search(r'episode=(\d+)', page_url)
        if url_match:
            ep_id = url_match.group(1)
            try:
                target_div = page.locator(f"div[data-scroll-id='{ep_id}']")
                if target_div.count() > 0:
                    text = target_div.inner_text()
                    num_match = re.search(r'(\d+)\s*эпизод', text, re.IGNORECASE)
                    if num_match:
                        return f"{int(num_match.group(1)):02d}"
            except Exception:
                pass

        try:
            active_div = page.locator("div.aex_ia.aex_fz").first
            if active_div.count() > 0:
                text = active_div.inner_text()
                num_match = re.search(r'(\d+)\s*эпизод', text, re.IGNORECASE)
                if num_match:
                    return f"{int(num_match.group(1)):02d}"
        except Exception:
            pass

        try:
            page_title = page.title()
            if page_title:
                title_match = re.search(r'(\d+)\s*(?:серия|эпизод|сезон)', page_title, re.IGNORECASE)
                if title_match:
                    return f"{int(title_match.group(1)):02d}"
        except Exception:
            pass

        try:
            body_text = page.locator("body").inner_text().lower()
            if "фильм" in body_text:
                headings = page.locator("h1, h2, .episode-title, .player-title").all()
                for h in headings:
                    if "фильм" in h.inner_text().lower():
                        return "Фильм"
        except Exception:
            pass

        return "01"

    def get_video_link(self, page_url):
        self.video_url = None
        self.video_type = None
        self.title = None
        self.episode_str = None
        self.blocked_count = 0

        with sync_playwright() as p:
            _file_dir = os.path.dirname(os.path.abspath(__file__))
            user_data_dir = os.path.join(_file_dir, "data", "browser_profile")
            os.makedirs(user_data_dir, exist_ok=True)

            extension_args = []
            if os.path.isdir(self.extension_path):
                extension_args = [
                    f"--disable-extensions-except={self.extension_path}",
                    f"--load-extension={self.extension_path}",
                ]
                print(f"[+] uBlock загружен из: {self.extension_path}")

            context = p.chromium.launch_persistent_context(
                user_data_dir,
                executable_path=self.chrome_path,
                headless=False,
                ignore_default_args=["--enable-automation", "disable-extensions"],
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                ] + extension_args,
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1280, "height": 720},
            )

        
            context.route("**/*", self._block_ads)

            page = context.pages[0]
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            page.on("request", self._intercept_network)

            print(f"[*] Переход на: {page_url}")
            page.goto(page_url, wait_until="domcontentloaded")

            self.title = self._extract_title(page)
            self.episode_str = self._extract_episode_info(page, page_url)
            print(f"[*] Тайтл: {self.title}")
            print(f"[*] Серия: {self.episode_str}")

            self.video_url = None

            try:
                page.wait_for_timeout(500)
                if self.video_type == "mp4":
                    print("[*] Пытаюсь запустить плеер...", flush=True)
                    page.wait_for_selector(
                        ".svg-inline--fa.fa-play > path", timeout=10000
                    )
                    page.locator(".svg-inline--fa.fa-play > path").first.click()

                    page.wait_for_timeout(2000)
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
                    page.click("play_button")
                    page.locator("iframe").content_frame.locator("a").click()
                    page.locator("iframe").content_frame.get_by_role(
                        "cell", name="360p"
                    ).locator("span").click()
                    page.locator("iframe").content_frame.get_by_text("720p").click()

                timeout = 30
                start_time = time.time()
                while not self.video_url and (time.time() - start_time < timeout):
                    page.wait_for_timeout(500)

            except Exception as e:
                print(f"[!] Ошибка при автоматизации действий: {e}")

            print(f"[*] Заблокировано рекламных запросов: {self.blocked_count}")
            context.close()

            if not self.video_url:
                raise Exception("[-] Не удалось поймать ссылку автоматически.")

            return self.video_url, self.video_type, self.title, self.episode_str