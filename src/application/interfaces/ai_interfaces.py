from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any
from PIL import Image
from src.domain.value_objects import BoundingBox, TextSegment

class ITextDetectionEngine(ABC):
    @abstractmethod
    def detect_layout(self, image: Image.Image) -> Dict[str, Any]:
        """
        Locates texts bounding boxes, paragraphs, layout structures, and tables.
        Returns a dict structured as:
        {
           "blocks": [ { "bbox": BoundingBox, "type": "paragraph" | "table" | "heading" } ],
           "tables": [ { "bbox": BoundingBox, "cells": [...] } ],
           "reading_order": [int] # indices of sorted blocks
        }
        """
        pass

class ITextRecognitionEngine(ABC):
    @abstractmethod
    def recognize_text(self, image: Image.Image, bbox: BoundingBox) -> Tuple[str, float]:
        """
        Recognizes text within a specific cropped bounding box of the image.
        Returns a tuple of (recognized_text, confidence_score).
        """
        pass
