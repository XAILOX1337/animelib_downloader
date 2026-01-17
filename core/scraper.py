from playwright.sync_api import sync_playwright

from config import HEADERS


class AnimeScraper:
    def __init__(self):
        self.video_url = None

    def _intercept_network(self, request):
        # Ищем URL, который содержит .mp4 и признак высокого качества
        if ".mp4" in request.url and ("_1080" in request.url or "_2160" in request.url):
            self.video_url = request.url
            print(f"[+] Найдена прямая ссылка: {self.video_url}")

    def get_video_link(self, page_url):
        with sync_playwright() as p:
            # Запускаем браузер (headless=True, если не хочешь видеть окно)
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(user_agent=HEADERS["User-Agent"])
            page = context.new_page()

            # Вешаем обработчик на все сетевые запросы
            page.on("request", self._intercept_network)

            print(f"[*] Переход на страницу: {page_url}")
            page.goto(page_url)

            # Ждем немного, чтобы плеер успел прогрузить ссылку
            # Можно добавить клик по кнопке Play, если ссылка не появляется
            page.wait_for_timeout(30000)

            browser.close()

            if not self.video_url:
                raise Exception("[-] Не удалось найти ссылку на MP4 файл.")

            return self.video_url
