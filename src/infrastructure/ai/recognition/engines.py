import logging
from typing import Tuple
from PIL import Image
from src.application.interfaces.ai_interfaces import ITextRecognitionEngine
from src.domain.value_objects import BoundingBox

logger = logging.getLogger(__name__)

class MockRecognitionEngine(ITextRecognitionEngine):
    """Fast simulated OCR recognizer for testing and CPU local systems."""
    def recognize_text(self, image: Image.Image, bbox: BoundingBox) -> Tuple[str, float]:
        # Generate some mock text with coordinates to simulate real recognition
        x_min, y_min = int(bbox.x_min), int(bbox.y_min)
        w, h = int(bbox.x_max - bbox.x_min), int(bbox.y_max - bbox.y_min)
        
        # Simple heuristics based on box size
        if w > 200 and h > 50:
            text = "Enterprise OCR Engine Integration Success"
        elif w > 100:
            text = f"Sample text block at ({x_min}, {y_min})"
        else:
            text = "OCR Engine"
            
        return text, 0.99


class EasyOCRRecognitionEngine(ITextRecognitionEngine):
    """EasyOCR implementation using PyTorch under the hood."""
    def __init__(self):
        try:
            import easyocr
            # Initialize reader; CPU mode by default, will auto-detect GPU
            self.reader = easyocr.Reader(['en'], gpu=True)
        except ImportError:
            logger.error("EasyOCR package is not installed. Run `pip install easyocr`.")
            raise RuntimeError("EasyOCR is not installed in the environment.")

    def recognize_text(self, image: Image.Image, bbox: BoundingBox) -> Tuple[str, float]:
        import numpy as np
        # Crop the bounding box area
        cropped = image.crop((bbox.x_min, bbox.y_min, bbox.x_max, bbox.y_max))
        # Convert PIL to numpy
        np_img = np.array(cropped)
        
        results = self.reader.recognize(np_img)
        if not results:
            return "", 0.0
            
        # Merge all recognized words in this block
        texts = [res[1] for res in results]
        confidences = [res[2] for res in results]
        
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        return " ".join(texts), avg_conf


class PaddleOCRRecognitionEngine(ITextRecognitionEngine):
    """PaddleOCR pluggable engine."""
    def __init__(self):
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        except ImportError:
            logger.error("PaddleOCR package is not installed. Run `pip install paddleocr`.")
            raise RuntimeError("PaddleOCR is not installed in the environment.")

    def recognize_text(self, image: Image.Image, bbox: BoundingBox) -> Tuple[str, float]:
        import numpy as np
        cropped = image.crop((bbox.x_min, bbox.y_min, bbox.x_max, bbox.y_max))
        np_img = np.array(cropped)
        
        result = self.ocr.ocr(np_img, cls=True)
        if not result or not result[0]:
            return "", 0.0
            
        texts = []
        confs = []
        for line in result[0]:
            texts.append(line[1][0])
            confs.append(line[1][1])
            
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        return " ".join(texts), avg_conf


class TrOCRRecognitionEngine(ITextRecognitionEngine):
    """HuggingFace TrOCR engine for high-accuracy single-line handwriting/printed text."""
    def __init__(self):
        try:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            import torch
            self.processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
            self.model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
        except ImportError:
            logger.error("transformers or torch is not installed.")
            raise RuntimeError("Transformers & Torch must be installed to run TrOCR.")

    def recognize_text(self, image: Image.Image, bbox: BoundingBox) -> Tuple[str, float]:
        cropped = image.crop((bbox.x_min, bbox.y_min, bbox.x_max, bbox.y_max))
        
        # TrOCR expects RGB PIL image inputs
        pixel_values = self.processor(images=cropped, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(self.device)
        
        generated_ids = self.model.generate(pixel_values)
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return generated_text, 0.95


def get_recognition_engine(engine_name: str) -> ITextRecognitionEngine:
    """Factory to retrieve recognition engine by key configuration name."""
    engine_name = engine_name.lower().strip()
    if engine_name == "easyocr":
        return EasyOCRRecognitionEngine()
    elif engine_name == "paddleocr":
        return PaddleOCRRecognitionEngine()
    elif engine_name == "trocr":
        return TrOCRRecognitionEngine()
    else:
        return MockRecognitionEngine()
