import re


class OCRNormalizer:
    """
    Нормализация строк после OCR.
    """

    # Частые замены символов
    REPLACEMENTS = {
        "—": "-",
        "–": "-",
        "«": '"',
        "»": '"',
        "|": "1",
        "§": "S",
        "€": "E",
    }

    @classmethod
    def normalize(cls, lines: list[str]) -> list[str]:

        normalized = []

        for line in lines:

            # Удаляем лишние пробелы
            line = re.sub(r"\s+", " ", line.strip())

            # Замена символов
            for old, new in cls.REPLACEMENTS.items():
                line = line.replace(old, new)

            # Запятая -> точка
            line = re.sub(r"(\d),(\d{2})", r"\1.\2", line)

            # "=1880.00" -> "1880.00"
            line = re.sub(r"=+", "", line)

            # "#1880.00" -> "1880.00"
            line = re.sub(r"#(?=\d)", "", line)

            # Несколько точек подряд
            line = re.sub(r"\.{2,}", ".", line)

            # Несколько пробелов
            line = re.sub(r"\s{2,}", " ", line)

            if line:
                normalized.append(line)

        return normalized