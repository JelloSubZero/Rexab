import re

from services.ocr.models import Product


class ProductParser:
    """
    Извлекает товары из OCR-текста.
    """

    # Цена в конце строки
    PRICE_PATTERN = re.compile(r"(\d+[.,]\d{2})$")

    # Количество в начале строки:
    # 2 MLEKO
    # 3x MLEKO
    # 2 x MLEKO
    QUANTITY_PATTERN = re.compile(
        r"^(\d+)\s*[xX]?\s+"
    )

    @classmethod
    def parse(cls, lines: list[str]) -> list[Product]:

        products: list[Product] = []

        for line in lines:

            line = line.strip()

            if not line:
                continue

            price_match = cls.PRICE_PATTERN.search(line)

            if not price_match:
                continue

            try:
                price = float(
                    price_match.group(1).replace(",", ".")
                )
            except ValueError:
                continue

            name = line[:price_match.start()].strip()

            quantity = 1

            quantity_match = cls.QUANTITY_PATTERN.match(name)

            if quantity_match:
                quantity = int(quantity_match.group(1))
                name = name[quantity_match.end():].strip()

            if len(name) < 2:
                continue

            products.append(
                Product(
                    name=name,
                    quantity=quantity,
                    price=price,
                )
            )

        return products