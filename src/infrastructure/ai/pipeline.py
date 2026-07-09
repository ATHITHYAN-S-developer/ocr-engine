import re
import logging
from PIL import Image
import io
from typing import Dict, Any, List, Tuple
from src.domain.value_objects import BoundingBox, TextSegment, OcrEngineConfig
from src.infrastructure.ai.preprocessor import ImagePreprocessor
from src.infrastructure.ai.detection.locate_anything import LocateAnythingDetectionEngine
from src.infrastructure.ai.recognition.engines import get_recognition_engine
from src.domain.exceptions import OcrProcessingException

logger = logging.getLogger(__name__)

class OcrPipelineCoordinator:
    """
    Orchestrates the entire OCR flow:
    PDF Converter -> Image Preprocessing -> LocateAnything Detection -> OCR Recognition -> 
    Layout Analysis -> Reading Order -> Table Detection -> Form Detection -> Entity Extraction ->
    Post Processing.
    """
    def __init__(self, recognition_engine_name: str = "mock"):
        self.preprocessor = ImagePreprocessor()
        self.detector = LocateAnythingDetectionEngine(use_mock_fallback=True)
        self.recognizer = get_recognition_engine(recognition_engine_name)

    def file_to_images(self, file_data: bytes, file_type: str) -> List[Image.Image]:
        """
        PDF Converter Stage.
        Converts PDF to PIL Images, or opens images directly.
        """
        file_type = file_type.upper().strip(".")
        if file_type == "PDF":
            try:
                from pdf2image import convert_from_bytes
                return convert_from_bytes(file_data)
            except Exception as e:
                logger.warning(f"Could not convert PDF using pdf2image (Poppler might be missing): {e}. Falling back to generating a mock image representation.")
                # Fallback: create a mock image with text details
                img = Image.new("RGB", (800, 1100), color=(255, 255, 255))
                return [img]
        else:
            try:
                return [Image.open(io.BytesIO(file_data))]
            except Exception as e:
                raise OcrProcessingException(f"Failed to load image: {e}")

    def run_pipeline(self, file_data: bytes, file_type: str, config: OcrEngineConfig) -> Tuple[str, Dict[str, Any], float]:
        # 1. PDF Converter
        images = self.file_to_images(file_data, file_type)
        
        all_text_blocks: List[str] = []
        pages_result: List[Dict[str, Any]] = []
        total_confidence = 0.0
        block_counter = 0

        # Loop through pages
        for page_idx, img in enumerate(images):
            # 2. Image Preprocessing
            prep_config = config.preprocessing_steps or {
                "deskew": True,
                "enhance_contrast": True,
                "normalize_brightness": True
            }
            preprocessed_img = self.preprocessor.preprocess(img, prep_config)
            
            # 3. LocateAnything Detection (handles Text Detection, BBoxes, Table Detection, Paragraphs)
            layout = self.detector.detect_layout(preprocessed_img)
            blocks = layout["blocks"]
            tables = layout["tables"]
            reading_order = layout["reading_order"] # Sorted block indexes
            
            page_blocks: List[Dict[str, Any]] = []
            page_text_segments: List[str] = []
            page_confidence = 0.0
            
            # 4 & 5 & 6 & 7. Pluggable OCR Recognition on detected blocks in Reading Order
            for block_idx in reading_order:
                block = next((b for b in blocks if b["id"] == block_idx), None)
                if not block:
                    continue
                
                bbox = block["bbox"]
                
                # Recognize text in block
                text, conf = self.recognizer.recognize_text(preprocessed_img, bbox)
                
                # Post Processing of text
                processed_text = self._post_process_text(text)
                
                page_confidence += conf
                page_text_segments.append(processed_text)
                
                page_blocks.append({
                    "id": block_counter,
                    "type": block["type"],
                    "bbox": {
                        "x_min": bbox.x_min,
                        "y_min": bbox.y_min,
                        "x_max": bbox.x_max,
                        "y_max": bbox.y_max
                    },
                    "text": processed_text,
                    "confidence": conf
                })
                block_counter += 1

            # 8. Table Detection mapping
            page_tables = []
            for t_idx, t in enumerate(tables):
                t_bbox = t["bbox"]
                # Detect text overlapping with cells
                cells_data = []
                for cell in t["cells"]:
                    cell_text, cell_conf = self.recognizer.recognize_text(preprocessed_img, cell)
                    cells_data.append({
                        "bbox": {"x_min": cell.x_min, "y_min": cell.y_min, "x_max": cell.x_max, "y_max": cell.y_max},
                        "text": cell_text
                    })
                page_tables.append({
                    "id": t_idx,
                    "bbox": {"x_min": t_bbox.x_min, "y_min": t_bbox.y_min, "x_max": t_bbox.x_max, "y_max": t_bbox.y_max},
                    "cells": cells_data
                })

            page_full_text = "\n".join(page_text_segments)
            all_text_blocks.append(page_full_text)
            
            # 9. Form Detection (Key-Value extraction)
            forms = self._detect_forms(page_blocks)
            
            # 10. Entity Extraction
            entities = self._extract_entities(page_full_text)
            
            avg_page_conf = page_confidence / len(reading_order) if reading_order else 1.0
            total_confidence += avg_page_conf

            pages_result.append({
                "page_number": page_idx + 1,
                "width": img.width,
                "height": img.height,
                "text": page_full_text,
                "blocks": page_blocks,
                "tables": page_tables,
                "forms": forms,
                "entities": entities,
                "confidence": avg_page_conf
            })

        document_full_text = "\n\n--- Page Break ---\n\n".join(all_text_blocks)
        avg_document_confidence = total_confidence / len(images) if images else 1.0

        # Global entities and tables aggregation
        global_tables: List[Dict[str, Any]] = []
        global_entities: List[Dict[str, Any]] = []
        for p in pages_result:
            global_tables.extend(p["tables"])
            global_entities.extend(p["entities"])

        structured_json = {
            "document_id": "", # Filled by application layer
            "pages": pages_result,
            "text": document_full_text,
            "tables": global_tables,
            "blocks": [b for p in pages_result for b in p["blocks"]],
            "entities": global_entities,
            "confidence": round(avg_document_confidence, 2)
        }

        return document_full_text, structured_json, avg_document_confidence

    def _post_process_text(self, text: str) -> str:
        """
        Post Processing Stage.
        Clean common OCR issues, remove extra spaces, standardise quotes.
        """
        # Remove multiple spaces
        text = re.sub(r'[ \t]+', ' ', text)
        # Normalize quotes
        text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        return text.strip()

    def _detect_forms(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Form Detection Stage.
        Heuristic key-value pairing based on proximity (e.g. "Key:" followed by "Value").
        """
        forms = []
        for i, block in enumerate(blocks):
            txt = block["text"]
            if ":" in txt and not txt.endswith(":"):
                parts = txt.split(":", 1)
                key = parts[0].strip()
                val = parts[1].strip()
                if len(key) < 50 and len(val) > 0:
                    forms.append({
                        "key": key,
                        "value": val,
                        "key_bbox": block["bbox"],
                        "value_bbox": block["bbox"]
                    })
        return forms

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Entity Extraction Stage.
        Identify key fields: emails, phones, dates, currency/invoice sums.
        """
        entities = []
        
        # Regex helpers
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_pattern = r'\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        date_pattern = r'\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
        amount_pattern = r'\b[A-Z]{3}\s?\d+(?:\.\d{2})?|\b\$\s?\d+(?:\.\d{2})?\b'

        emails = re.findall(email_pattern, text)
        for e in emails:
            entities.append({"type": "EMAIL", "value": e})

        phones = re.findall(phone_pattern, text)
        for p in phones:
            if len(p) > 7: # filter short numbers
                entities.append({"type": "PHONE", "value": p.strip()})

        dates = re.findall(date_pattern, text)
        for d in dates:
            entities.append({"type": "DATE", "value": d})

        amounts = re.findall(amount_pattern, text)
        for a in amounts:
            entities.append({"type": "AMOUNT", "value": a})

        return entities
