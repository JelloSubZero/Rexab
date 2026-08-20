import logging
import os
import re
import tempfile

import cv2

from services.ocr.cropper import ImageCropper
from services.ocr.engine import OCREngine
from services.ocr.locator import OCRLocator

logger = logging.getLogger(__name__)


class TotalExtractor:

    def __init__(self):
        self.locator = OCRLocator()
        self.engine = OCREngine()

    def extract(self, image_path: str) -> float | None:

        area = self.locator.find_total_area(image_path)

        logger.debug("Total area: %s", area)

        if area is None:
            return None

        crop = ImageCropper.crop(image_path, area)

        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

        cv2.imwrite(temp_path, crop)

        try:
            text = self.engine.recognize(
                temp_path,
                psm=11,
            )

            logger.debug("Total OCR text: %r", text)

        finally:
            os.remove(temp_path)

        # Ищем все суммы вида:
        # 34500.00
        # 34 500.00
        # 34500. 00
        # 34 500,00
        numbers = re.findall(
            r"\d[\d\s]*[.,]\s*\d{2}",
            text,
        )

        logger.debug("Candidate numbers: %s", numbers)

        if not numbers:
            return None

        value = numbers[-1]

        value = (
            value.replace(" ", "")
                 .replace(",", ".")
        )

        logger.debug("Parsed value: %s", value)

        try:
            return float(value)
        except ValueError:
            return None