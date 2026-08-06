from pathlib import Path

from PIL import Image
import pytesseract
from pytesseract import Output

from config import OCR_LANGUAGES, TESSERACT_PATH


class OCRLocator:

    TOTAL_KEYWORDS = (
        "ИТОГ",
        "TOTAL",
        "SUMA",
        "RAZEM",
        "ВСЕГО",
        "DO ZAPŁATY",
        "DO ZAPLATY",
    )

    def __init__(self):
        if TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

    def find_total_area(self, image_path: str | Path):

        image = Image.open(image_path)

        data = pytesseract.image_to_data(
            image,
            lang=OCR_LANGUAGES,
            config="--oem 3 --psm 6",
            output_type=Output.DICT,
        )

        # Собираем слова в строки
        lines = {}

        count = len(data["text"])

        for i in range(count):

            text = data["text"][i].strip()

            if not text:
                continue

            key = (
                data["block_num"][i],
                data["par_num"][i],
                data["line_num"][i],
            )

            if key not in lines:

                lines[key] = {
                    "text": [],
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "right": data["left"][i] + data["width"][i],
                    "bottom": data["top"][i] + data["height"][i],
                }

            line = lines[key]

            line["text"].append(text)

            line["left"] = min(line["left"], data["left"][i])
            line["top"] = min(line["top"], data["top"][i])

            line["right"] = max(
                line["right"],
                data["left"][i] + data["width"][i],
            )

            line["bottom"] = max(
                line["bottom"],
                data["top"][i] + data["height"][i],
            )

        # Ищем строку с итогом
        for line in lines.values():

            text = " ".join(line["text"]).upper()

            if any(keyword in text for keyword in self.TOTAL_KEYWORDS):

                return {
                    "text": text,
                    "left": line["left"],
                    "top": line["top"],
                    "right": line["right"],
                    "bottom": line["bottom"],
                }

        return None