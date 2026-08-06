from pathlib import Path

import cv2


class ImageCropper:

    @staticmethod
    def crop(image_path: str | Path, area: dict):

        image = cv2.imread(str(image_path))

        if image is None:
            raise FileNotFoundError(image_path)

        h, w = image.shape[:2]

        pad_x = 20
        pad_y = 20

        x1 = max(area["left"] - pad_x, 0)
        y1 = max(area["top"] - pad_y, 0)

        x2 = min(area["right"] + pad_x, w)
        y2 = min(area["bottom"] + pad_y, h)

        return image[y1:y2, x1:x2]