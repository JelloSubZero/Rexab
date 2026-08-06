import re


class TotalParser:
    """
    Универсальный поиск итоговой суммы чека.
    """

    # Ключевые слова, которые часто встречаются перед итоговой суммой
    TOTAL_KEYWORDS = {
        "TOTAL",
        "SUM",
        "SUMA",
        "RAZEM",
        "ИТОГО",
        "ВСЕГО",
        "TOTAL:",
        "AMOUNT",
        "TO PAY",
        "BALANCE",
    }

    # Любое число вида 123.45 или 123,45
    PRICE_PATTERN = re.compile(r"(\d+[.,]\d{2})")

    @classmethod
    def parse(cls, lines: list[str]) -> float | None:

        # Сначала ищем строки с ключевыми словами
        for line in reversed(lines):

            upper = line.upper()

            if any(keyword in upper for keyword in cls.TOTAL_KEYWORDS):

                match = cls.PRICE_PATTERN.search(upper)

                if match:
                    return float(match.group(1).replace(",", "."))

        # Если не нашли — берем последнее число,
        # похожее на денежную сумму
        for line in reversed(lines):

            matches = cls.PRICE_PATTERN.findall(line)

            if matches:
                return float(matches[-1].replace(",", "."))

        return None