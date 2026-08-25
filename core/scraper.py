from playwright.sync_api import sync_playwright
import time
import os
import re
from config import HEADERS


class AnimeScraper:
    def __init__(self):
        self.video_url = None
        self.video_type = None
        self.title = None
        self.episode_str = None
        # Путь к распакованному AdBlock
        self.extension_path = os.path.abspath("core/extensions/adblock")
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.user_data_dir = r"C:\Users\klim\AppData\Local\Google\Chrome\User Data"

    def _intercept_network(self, request):
        url = request.url
        if ".mp4" in url and ("_1080" in url or "_2160" in url or "_1004" in url):
            self.video_url = url
            self.video_type = "mp4"
        elif ".m3u8" in url and ("720" in url or "480" in url):
            self.video_url = url
            self.video_type = "m3u8"

    @staticmethod
    def _sanitize_filename(name):
        """Удалить символы, недопустимые в именах файлов (Windows + Linux)."""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '')
        return name.strip('. ')

    def _extract_title(self, page):
        """
        Извлечь название аниме. Мультистратегия:
          1) h1 > a  — основной (подтверждённый HTML)
          2) og:title — мета-тег
          3) <title> — с очисткой от мусора
        """
        # Стратегия 1: h1 > a
        try:
            title_el = page.locator("h1 a").first
            title_el.wait_for(state="visible", timeout=5000)
            raw_title = title_el.inner_text().strip()
            if raw_title:
                return self._sanitize_filename(raw_title)
        except Exception:
            pass

        # Стратегия 2: og:title
        try:
            og_title = page.locator('meta[property="og:title"]').get_attribute("content")
            if og_title:
                return self._sanitize_filename(og_title.strip())
        except Exception:
            pass

        # Стратегия 3: <title> тег (обычно «Тайтл — Анимелиб» или «Тайтл — смотреть онлайн»)
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
        """
        Извлечь номер серии из страницы.
        Возвращает строку вида '01', '12', или 'Фильм'.
        """
        # Стратегия 1: Извлечь episode=67157 из URL, найти div с ссылкой
        # содержащей тот же episode=ID (надёжнее чем матчить ID div-а)
        url_match = re.search(r'episode=(\d+)', page_url)
        if url_match:
            ep_id = url_match.group(1)
            try:
                ep_divs = page.locator("div[id^='episode_']").all()
                for div in ep_divs:
                    links = div.locator("a").all()
                    for link in links:
                        href = link.get_attribute("href") or ""
                        if f"episode={ep_id}" in href:
                            spans = div.locator("span").all()
                            for span in spans:
                                text = span.inner_text().strip()
                                num_match = re.search(r'(\d+)\s*эпизод', text, re.IGNORECASE)
                                if num_match:
                                    return f"{int(num_match.group(1)):02d}"
            except Exception:
                pass

        # Стратегия 2: Ищем активную серию в списке (обычно имеет класс-маркер)
        try:
            ep_divs = page.locator("div[id^='episode_']").all()
            for div in ep_divs:
                class_attr = (div.get_attribute("class") or "").lower()
                is_active = any(
                    marker in class_attr
                    for marker in ["active", "current", "selected", "playing", "aex_active"]
                )
                if not is_active:
                    continue
                spans = div.locator("span").all()
                for span in spans:
                    text = span.inner_text().strip()
                    num_match = re.search(r'(\d+)\s*эпизод', text, re.IGNORECASE)
                    if num_match:
                        return f"{int(num_match.group(1)):02d}"
        except Exception:
            pass

        # Стратегия 3: Любой текст "N эпизод" на странице (фоллбэк)
        try:
            ep_divs = page.locator("div[id^='episode_']").all()
            for div in ep_divs:
                spans = div.locator("span").all()
                for span in spans:
                    text = span.inner_text().strip()
                    num_match = re.search(r'(\d+)\s*эпизод', text, re.IGNORECASE)
                    if num_match:
                        return f"{int(num_match.group(1)):02d}"
        except Exception:
            pass

        # Стратегия 4: Проверяем, не фильм ли это
        try:
            body_text = page.locator("body").inner_text().lower()
            if "фильм" in body_text:
                headings = page.locator("h1, h2, .episode-title, .player-title").all()
                for h in headings:
                    if "фильм" in h.inner_text().lower():
                        return "Фильм"
        except Exception:
            pass

        return "01"  # Итоговый фоллбэк

    def get_video_link(self, page_url):
        # Сброс состояния — КРИТИЧНО при повторных вызовах
        self.video_url = None
        self.video_type = None
        self.title = None
        self.episode_str = None

        with sync_playwright() as p:

            user_data_dir = os.path.abspath("data/browser_profile")

            # ФИКС: расширения теперь реально передаются в args
            extension_args = []
            if os.path.exists(self.extension_path):
                extension_args = [
                    f"--disable-extensions-except={self.extension_path}",
                    f"--load-extension={self.extension_path}",
                ]

            context = p.chromium.launch_persistent_context(
                user_data_dir,
                executable_path=self.chrome_path,
                headless=False,
                ignore_default_args=["--enable-automation"],
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                ] + extension_args,
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1280, "height": 720},
            )

            page = context.pages[0]

            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            page.on("request", self._intercept_network)

            print(f"[*] Переход на: {page_url}")
            page.goto(page_url, wait_until="domcontentloaded")

            # --- Извлечение метаданных ---
            self.title = self._extract_title(page)
            self.episode_str = self._extract_episode_info(page, page_url)
            print(f"[*] Тайтл: {self.title}")
            print(f"[*] Серия: {self.episode_str}")

            # ============================================================
            # КРИТИЧЕСКИЙ ФИКС: сброс URL, пойманного при загрузке страницы
            # Без этого при 2+, 3+ запуске перехватывается старый URL
            # из persistent profile (кеш, service worker, cleanup
            # предыдущей сессии), и цикл ожидания на строке 140
            # мгновенно выходит, не дожидаясь настоящего URL.
            # video_type сохраняем — он нужен для выбора ветки автоматизации.
            # ============================================================
            self.video_url = None

            try:
                page.wait_for_timeout(500)
                # 1. Кликаем Play
                if self.video_type == "mp4":

                    print("[*] Пытаюсь запустить плеер...", flush=True)
                    page.wait_for_selector(
                        ".svg-inline--fa.fa-play > path", timeout=10000
                    )
                    page.locator(".svg-inline--fa.fa-play > path").first.click()

                    # 2. Выбор качества
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
                    print("--- DEBUG:--")
                    page.click("play_button")
                    page.locator("iframe").content_frame.locator("a").click()
                    page.locator("iframe").content_frame.get_by_role(
                        "cell", name="360p"
                    ).locator("span").click()
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

            return self.video_url, self.video_type, self.title, self.episode_str