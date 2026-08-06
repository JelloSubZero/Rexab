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
QR_DIR = STATIC_DIR / "qr"
RECEIPTS_DIR = STATIC_DIR / "receipts"
LOGS_DIR = BASE_DIR / "logs"

# Автоматическое создание папок
QR_DIR.mkdir(parents=True, exist_ok=True)
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "YourBotUsername",
)