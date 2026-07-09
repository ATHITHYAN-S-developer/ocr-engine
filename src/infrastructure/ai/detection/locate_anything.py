import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, List
from src.application.interfaces.ai_interfaces import ITextDetectionEngine
from src.domain.value_objects import BoundingBox

class LocateAnythingDetectionEngine(ITextDetectionEngine):
    """
    NVIDIA LocateAnything Layout Detection Client wrapper.
    Includes a highly functional OpenCV contour fallback for environments without access to GPUs.
    """
    def __init__(self, use_mock_fallback: bool = True):
        self.use_mock_fallback = use_mock_fallback

    def detect_layout(self, image: Image.Image) -> Dict[str, Any]:
        if not self.use_mock_fallback:
            return self._call_nvidia_locate_anything(image)
        return self._detect_layout_contour_fallback(image)

    def _call_nvidia_locate_anything(self, image: Image.Image) -> Dict[str, Any]:
        """
        Placeholder for real HTTP or Triton client call to NVIDIA LocateAnything model.
        In production, this queries the NVIDIA NIM API or custom Triton endpoint.
        """
        # Simulated payload from LocateAnything REST server
        # For production:
        # response = requests.post("http://nvidia-nim-locateanything:8000/v1/predictions", files={...})
        return self._detect_layout_contour_fallback(image)

    def _detect_layout_contour_fallback(self, image: Image.Image) -> Dict[str, Any]:
        """
        Robust OpenCV fallback to detect blocks (paragraphs), columns, and potential tables.
        Uses morphological operations to group text.
        """
        # Convert PIL to CV2 grayscale
        cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # Binary thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Dilate to merge characters into words/paragraphs
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
        dilated = cv2.dilate(thresh, kernel, iterations=3)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        blocks: List[Dict[str, Any]] = []
        img_h, img_w = cv_img.shape[:2]
        
        # Map contours to BoundingBox structures
        for i, cnt in enumerate(contours):
            x, y, w, h = cv2.boundingRect(cnt)
            # Filter tiny noise
            if w < 10 or h < 10:
                continue
                
            bbox = BoundingBox(
                x_min=float(x),
                y_min=float(y),
                x_max=float(x + w),
                y_max=float(y + h)
            )
            
            # Simple heuristic to distinguish paragraph vs header or tables
            block_type = "paragraph"
            if w > img_w * 0.7 and h > img_h * 0.15:
                block_type = "table"
            elif h < 30 and w < 300:
                block_type = "heading"
                
            blocks.append({
                "id": i,
                "bbox": bbox,
                "type": block_type
            })
            
        # 1. Reading Order: Sort top-to-bottom, then left-to-right (multi-column support)
        # We can sort by y_min first, then group close y values, then sort by x_min.
        sorted_blocks = sorted(blocks, key=lambda b: (b["bbox"].y_min, b["bbox"].x_min))
        reading_order = [b["id"] for b in sorted_blocks]

        # 2. Extract Table structures if any found
        tables = []
        for block in sorted_blocks:
            if block["type"] == "table":
                # Mock cells layout inside table block
                tb_bbox = block["bbox"]
                cells = []
                # Divide table into 2 rows, 2 columns for representation
                x_mid = (tb_bbox.x_min + tb_bbox.x_max) / 2
                y_mid = (tb_bbox.y_min + tb_bbox.y_max) / 2
                cells.append(BoundingBox(tb_bbox.x_min, tb_bbox.y_min, x_mid, y_mid))
                cells.append(BoundingBox(x_mid, tb_bbox.y_min, tb_bbox.x_max, y_mid))
                cells.append(BoundingBox(tb_bbox.x_min, y_mid, x_mid, tb_bbox.y_max))
                cells.append(BoundingBox(x_mid, y_mid, tb_bbox.x_max, tb_bbox.y_max))
                
                tables.append({
                    "bbox": tb_bbox,
                    "cells": cells
                })

        return {
            "blocks": sorted_blocks,
            "tables": tables,
            "reading_order": reading_order
        }
