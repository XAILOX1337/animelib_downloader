import os

# Заголовки из твоего cURL запроса
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Referer": "https://v3.animelib.org/",
    "sec-ch-ua-platform": '"Windows"',
}

# Настройки путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "data", "temp")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

# Настройки Real-CUGAN
CUGAN_CONFIG = {
    "scale": 2,  # Во сколько раз увеличиваем (2, 3, 4)
    "noise": 2,  # Уровень очистки шума (-1, 0, 1, 2, 3)
    "gpuid": 0,  # ID видеокарты (обычно 0)
}

# Создаем папки, если их нет
for path in [TEMP_DIR, OUTPUT_DIR]:
    os.makedirs(path, exist_ok=True)
