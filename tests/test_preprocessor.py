import unittest
import numpy as np
from PIL import Image
from src.infrastructure.ai.preprocessor import ImagePreprocessor

class TestImagePreprocessor(unittest.TestCase):
    def setUp(self):
        self.preprocessor = ImagePreprocessor()
        # Create a simple white PIL image with a black box for testing
        self.test_img = Image.new("RGB", (300, 300), color=(255, 255, 255))
        # Draw a small square inside the image
        img_arr = np.array(self.test_img)
        img_arr[100:150, 100:150] = [0, 0, 0] # black box
        self.test_img = Image.fromarray(img_arr)

    def test_conversion_helpers(self):
        cv_img = self.preprocessor.pil_to_cv(self.test_img)
        self.assertEqual(cv_img.shape, (300, 300, 3))
        
        pil_img = self.preprocessor.cv_to_pil(cv_img)
        self.assertEqual(pil_img.size, (300, 300))

    def test_preprocessing_flow(self):
        config = {
            "deskew": True,
            "denoise": False,
            "enhance_contrast": True,
            "normalize_brightness": True,
            "sharpen": True
        }
        processed = self.preprocessor.preprocess(self.test_img, config)
        self.assertEqual(processed.size, (300, 300))
        self.assertIsInstance(processed, Image.Image)

    def test_resize(self):
        cv_img = self.preprocessor.pil_to_cv(self.test_img)
        resized_cv = self.preprocessor.resize(cv_img, width=150, height=150)
        self.assertEqual(resized_cv.shape[:2], (150, 150))
