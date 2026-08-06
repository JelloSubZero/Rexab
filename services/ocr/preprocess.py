from pathlib import Path

import cv2
import numpy as np


class ImagePreprocessor:
    """
    Предобработка изображения для OCR.
    """

    SCALE = 3

    @classmethod
    def preprocess(cls, image_path: str | Path) -> np.ndarray:

        image = cv2.imread(str(image_path))

        if image is None:
            raise FileNotFoundError(
                f"Не удалось открыть изображение: {image_path}"
            )

        # Оттенки серого
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        # Увеличиваем изображение
        gray = cv2.resize(
            gray,
            None,
            fx=cls.SCALE,
            fy=cls.SCALE,
            interpolation=cv2.INTER_CUBIC,
        )

        # Убираем шум
        gray = cv2.fastNlMeansDenoising(
            gray,
            None,
            h=15,
        )

        # Повышаем локальный контраст
        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8),
        )

        gray = clahe.apply(gray)

        # Бинаризация
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            15,
        )

        # Небольшая морфологическая обработка
        kernel = np.ones((2, 2), np.uint8)

        binary = cv2.morphologyEx(
            binary,
            cv2.MORPH_OPEN,
            kernel,
        )

        return binary