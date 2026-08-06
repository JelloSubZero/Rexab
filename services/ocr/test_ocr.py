from pathlib import Path

from services.ocr.ocr_service import OCRService


def main():
    image_path = Path("static/receipts/test.jpg")

    if not image_path.exists():
        print(f"Файл не найден: {image_path}")
        return

    ocr = OCRService()

    result = ocr.process(str(image_path))

    print("\n========== RAW TEXT ==========\n")
    print(result.text)

    print("\n========== LINES ==========\n")
    for line in result.lines:
        print(line)

    print("\n========== TOTAL ==========\n")
    print(result.receipt.total)

    print("\n========== PRODUCTS ==========\n")

    if not result.receipt.products:
        print("Товары не найдены")
    else:
        for index, product in enumerate(result.receipt.products, start=1):
            print(
                f"{index}. "
                f"{product.name} | "
                f"Количество: {product.quantity} | "
                f"Цена: {product.price}"
            )


if __name__ == "__main__":
    main()