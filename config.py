from pathlib import Path
from dotenv import load_dotenv
import os

# Корневая папка проекта
BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

TESSERACT_PATH = os.getenv("TESSERACT_PATH")

OCR_LANGUAGES = os.getenv(
    "OCR_LANGUAGES",
    "pol+eng+rus",
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{BASE_DIR / 'split_receipt.db'}"
)

STATIC_DIR = BASE_DIR / "static"
RECEIPTS_DIR = STATIC_DIR / "receipts"
LOGS_DIR = BASE_DIR / "logs"

# Автоматическое создание папок
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "YourBotUsername",
)

# Секрет для подписи JWT веб-сессий. В проде обязателен собственный
# случайный секрет (например: python -c "import secrets; print(secrets.token_hex(32))");
# значение по умолчанию подходит только для локальной разработки.
JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "dev-insecure-secret-change-me",
)

JWT_ALGORITHM = "HS256"

JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "1440")
)

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000",
    ).split(",")
    if origin.strip()
]

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()