from services.ocr.engine import OCREngine
from services.ocr.models import OCRResult, ReceiptData
from services.ocr.normalizer import OCRNormalizer
from services.ocr.parser import OCRParser
from services.ocr.product_parser import ProductParser
from services.ocr.total_extractor import TotalExtractor


class OCRService:

    def __init__(self):
        self.engine = OCREngine()
        self.total_extractor = TotalExtractor()

    def process(self, image_path: str) -> OCRResult:
        """
        Полный цикл обработки чека.
        """

        # Первый OCR всего чека
        text = self.engine.recognize(image_path)

        # Разбиваем на строки
        lines = OCRParser.parse(text)

        # Нормализуем
        lines = OCRNormalizer.normalize(lines)

        # Пока оставляем товары как есть
        products = ProductParser.parse(lines)

        # Новый алгоритм определения общей суммы
        total = self.total_extractor.extract(image_path)

        print("========== TOTAL ==========")
        print(total)

        receipt = ReceiptData(
            total=total,
            products=products,
            raw_text=text,
        )

        return OCRResult(
            success=True,
            text=text,
            lines=lines,
            receipt=receipt,
        )