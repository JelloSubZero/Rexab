import re


class OCRParser:

    @staticmethod
    def parse(text: str) -> list[str]:
        """
        Преобразует сырой OCR-текст
        в список очищенных строк.
        """

        if not text:
            return []

        lines = []

        for line in text.splitlines():

            # Удаляем лишние пробелы
            line = line.strip()

            # Несколько пробелов -> один
            line = re.sub(r"\s+", " ", line)

            # Пустые строки пропускаем
            if not line:
                continue

            lines.append(line)

        return lines