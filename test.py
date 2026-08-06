import cv2
import pytesseract
from PIL import Image

from services.ocr.cropper import ImageCropper
from services.ocr.locator import OCRLocator

IMAGE_PATH = "test.jpg"      # путь к чеку


def main():

    locator = OCRLocator()

    area = locator.find_total_area(IMAGE_PATH)

    print("========== AREA ==========")
    print(area)

    if area is None:
        print("Итог не найден")
        return

    crop = ImageCropper.crop(
        IMAGE_PATH,
        area,
    )

    cv2.imwrite("debug_total_crop.png", crop)

    print("debug_total_crop.png сохранен")

    print()

    print("========== OCR PSM 6 ==========")

    image = Image.open("debug_total_crop.png")

    text = pytesseract.image_to_string(
        image,
        lang="rus+eng",
        config="--oem 3 --psm 6",
    )

    print(repr(text))
    print(text)

    print()

    print("========== OCR PSM 7 ==========")

    text = pytesseract.image_to_string(
        image,
        lang="rus+eng",
        config="--oem 3 --psm 7",
    )

    print(repr(text))
    print(text)

    print()

    print("========== OCR PSM 11 ==========")

    text = pytesseract.image_to_string(
        image,
        lang="rus+eng",
        config="--oem 3 --psm 11",
    )

    print(repr(text))
    print(text)


if __name__ == "__main__":
    main()