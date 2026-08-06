from pathlib import Path

import qrcode

from config import BOT_USERNAME, QR_DIR


class QRService:

    @staticmethod
    def generate(room_code: str) -> Path:

        link = f"https://t.me/{BOT_USERNAME}?start={room_code}"

        file_path = QR_DIR / f"{room_code}.png"

        img = qrcode.make(link)

        img.save(file_path)

        return file_path