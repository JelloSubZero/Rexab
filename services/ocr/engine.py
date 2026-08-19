from pathlib import Path

import cv2
import pytesseract

from config import OCR_LANGUAGES, TESSERACT_PATH
import numpy as np
from PIL import Image


class OCREngine:

    def __init__(self):
        if TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

    def recognize_image(self, image: np.ndarray) -> str:

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB,
        )

        image = Image.fromarray(image)

        text = pytesseract.image_to_string(
            image,
            lang=OCR_LANGUAGES,
            config="--oem 3 --psm 7",
        )

        return text.strip()

    def recognize(
            self,
            image_path: str | Path,
            psm: int = 6,
        ) -> str:

        image = Image.open(image_path)

        text = pytesseract.image_to_string(
                image,
                lang=OCR_LANGUAGES,
            config=f"--oem 3 --psm {psm}",
        )

        return text.strip()