import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional

class ImagePreprocessor:
    @staticmethod
    def pil_to_cv(image: Image.Image) -> np.ndarray:
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def cv_to_pil(cv_img: np.ndarray) -> Image.Image:
        return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))

    def deskew(self, cv_img: np.ndarray) -> np.ndarray:
        """Corrects image skew angle."""
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bitwise_not(gray)
        coords = np.column_stack(np.where(gray > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        # minAreaRect returns angle in [-90, 0) range
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        (h, w) = cv_img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(cv_img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated

    def denoise(self, cv_img: np.ndarray) -> np.ndarray:
        """Removes background noise."""
        return cv2.fastNlMeansDenoisingColored(cv_img, None, 10, 10, 7, 21)

    def resize(self, cv_img: np.ndarray, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:
        """Resizes the image preserving aspect ratio if only one dimension is given."""
        h, w = cv_img.shape[:2]
        if width is None and height is None:
            return cv_img
        if width is not None and height is not None:
            return cv2.resize(cv_img, (width, height), interpolation=cv2.INTER_CUBIC)
        if width is not None:
            r = width / float(w)
            dim = (width, int(h * r))
        else:
            r = height / float(h)
            dim = (int(w * r), height)
        return cv2.resize(cv_img, dim, interpolation=cv2.INTER_CUBIC)

    def enhance_contrast(self, cv_img: np.ndarray) -> np.ndarray:
        """Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) for contrast enhancement."""
        lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    def normalize_brightness(self, cv_img: np.ndarray) -> np.ndarray:
        """Normalizes brightness levels using HSV threshold adjustment."""
        hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = cv2.normalize(v, None, 0, 255, cv2.NORM_MINMAX)
        hsv_normalized = cv2.merge((h, s, v))
        return cv2.cvtColor(hsv_normalized, cv2.COLOR_HSV2BGR)

    def correct_rotation(self, cv_img: np.ndarray, angle: float) -> np.ndarray:
        """Rotates the image by a fixed degree value (90, 180, 270, etc)."""
        if angle == 90:
            return cv2.rotate(cv_img, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(cv_img, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return cv_img

    def sharpen(self, cv_img: np.ndarray) -> np.ndarray:
        """Applies a sharpening convolution filter."""
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        return cv2.filter2D(cv_img, -1, kernel)

    def adaptive_threshold(self, cv_img: np.ndarray) -> np.ndarray:
        """Converts to grayscale and applies adaptive thresholding."""
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    def preprocess(self, image: Image.Image, config: Optional[Dict[str, Any]] = None) -> Image.Image:
        """Applies configuration-driven preprocessing pipeline on a PIL Image."""
        if not config:
            config = {
                "deskew": True,
                "denoise": False,
                "enhance_contrast": True,
                "normalize_brightness": True,
                "sharpen": True
            }
            
        cv_img = self.pil_to_cv(image)

        if config.get("denoise"):
            cv_img = self.denoise(cv_img)
        if config.get("normalize_brightness"):
            cv_img = self.normalize_brightness(cv_img)
        if config.get("enhance_contrast"):
            cv_img = self.enhance_contrast(cv_img)
        if config.get("deskew"):
            cv_img = self.deskew(cv_img)
        if "rotate_angle" in config:
            cv_img = self.correct_rotation(cv_img, config["rotate_angle"])
        if config.get("sharpen"):
            cv_img = self.sharpen(cv_img)
        if config.get("adaptive_threshold"):
            cv_img = self.adaptive_threshold(cv_img)
        if "resize" in config:
            res_conf = config["resize"]
            cv_img = self.resize(cv_img, res_conf.get("width"), res_conf.get("height"))

        return self.cv_to_pil(cv_img)
