"""
CogniFy OCR Service
Optical Character Recognition for images and scanned documents
Created with love by Angela & David - 1 January 2026
"""

import os
import logging
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings

logger = logging.getLogger(__name__)


class OCREngine(str, Enum):
    """Available OCR engines"""
    TESSERACT = "tesseract"
    PADDLEOCR = "paddleocr"
    EASYOCR = "easyocr"


@dataclass
class OCRResult:
    """OCR extraction result"""
    text: str
    confidence: float
    language: str
    boxes: List[Dict[str, Any]]  # Bounding boxes for detected text
    engine: str


class OCRService:
    """
    OCR Service for extracting text from images.

    Supports multiple engines with fallback:
    1. Tesseract (default, widely available)
    2. PaddleOCR (good for Asian languages)
    3. EasyOCR (fallback)
    """

    def __init__(
        self,
        engine: OCREngine = OCREngine.TESSERACT,
        languages: List[str] = None,
    ):
        self.engine = engine
        self.languages = languages or ["eng", "tha"]  # English + Thai
        self._tesseract = None
        self._paddleocr = None
        self._easyocr = None

    async def extract_text(
        self,
        image_path: str,
        preprocess: bool = True,
    ) -> OCRResult:
        """
        Extract text from an image file.

        Args:
            image_path: Path to the image file
            preprocess: Whether to preprocess image for better OCR

        Returns:
            OCRResult with extracted text and metadata
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Try primary engine, fallback to others
        engines = [self.engine, OCREngine.TESSERACT, OCREngine.EASYOCR]

        for engine in engines:
            try:
                if engine == OCREngine.TESSERACT:
                    return await self._extract_with_tesseract(image_path, preprocess)
                elif engine == OCREngine.PADDLEOCR:
                    return await self._extract_with_paddleocr(image_path)
                elif engine == OCREngine.EASYOCR:
                    return await self._extract_with_easyocr(image_path)
            except ImportError as e:
                logger.warning(f"OCR engine {engine} not available: {e}")
                continue
            except Exception as e:
                logger.error(f"OCR extraction failed with {engine}: {e}")
                continue

        raise RuntimeError("No OCR engine available. Install tesseract, paddleocr, or easyocr.")

    async def _extract_with_tesseract(
        self,
        image_path: str,
        preprocess: bool = True,
    ) -> OCRResult:
        """Extract text using Tesseract OCR"""
        try:
            import pytesseract
            from PIL import Image
            import cv2
            import numpy as np
        except ImportError:
            raise ImportError(
                "Tesseract dependencies not installed. "
                "Install with: pip install pytesseract pillow opencv-python"
            )

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            # Try with PIL for more format support
            pil_image = Image.open(image_path)
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        if preprocess:
            image = self._preprocess_image(image)

        # Convert to PIL for tesseract
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # Configure Tesseract
        lang = "+".join(self.languages)
        config = '--psm 6'  # Assume uniform block of text

        # Get text with confidence
        try:
            data = pytesseract.image_to_data(
                pil_image,
                lang=lang,
                config=config,
                output_type=pytesseract.Output.DICT
            )
        except pytesseract.TesseractNotFoundError:
            raise ImportError(
                "Tesseract not found. Install with: brew install tesseract tesseract-lang"
            )

        # Extract text and boxes
        text_parts = []
        boxes = []
        confidences = []

        for i, word in enumerate(data['text']):
            if word.strip():
                conf = float(data['conf'][i])
                if conf > 0:  # Filter out low confidence
                    text_parts.append(word)
                    confidences.append(conf)
                    boxes.append({
                        'text': word,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': conf,
                    })

        text = ' '.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return OCRResult(
            text=text,
            confidence=avg_confidence / 100,  # Normalize to 0-1
            language=lang,
            boxes=boxes,
            engine="tesseract",
        )

    async def _extract_with_paddleocr(self, image_path: str) -> OCRResult:
        """Extract text using PaddleOCR (good for Asian languages)"""
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError(
                "PaddleOCR not installed. "
                "Install with: pip install paddlepaddle paddleocr"
            )

        if self._paddleocr is None:
            # Use Thai+English by default
            self._paddleocr = PaddleOCR(
                use_angle_cls=True,
                lang='th',  # Thai includes English
                show_log=False,
            )

        result = self._paddleocr.ocr(image_path, cls=True)

        text_parts = []
        boxes = []
        confidences = []

        if result and result[0]:
            for line in result[0]:
                box, (text, conf) = line
                text_parts.append(text)
                confidences.append(conf)
                boxes.append({
                    'text': text,
                    'box': box,
                    'confidence': conf,
                })

        text = ' '.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return OCRResult(
            text=text,
            confidence=avg_confidence,
            language='th+en',
            boxes=boxes,
            engine="paddleocr",
        )

    async def _extract_with_easyocr(self, image_path: str) -> OCRResult:
        """Extract text using EasyOCR"""
        try:
            import easyocr
        except ImportError:
            raise ImportError(
                "EasyOCR not installed. "
                "Install with: pip install easyocr"
            )

        if self._easyocr is None:
            self._easyocr = easyocr.Reader(['en', 'th'])

        results = self._easyocr.readtext(image_path)

        text_parts = []
        boxes = []
        confidences = []

        for (bbox, text, conf) in results:
            text_parts.append(text)
            confidences.append(conf)
            boxes.append({
                'text': text,
                'box': bbox,
                'confidence': conf,
            })

        text = ' '.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return OCRResult(
            text=text,
            confidence=avg_confidence,
            language='th+en',
            boxes=boxes,
            engine="easyocr",
        )

    def _preprocess_image(self, image) -> Any:
        """
        Preprocess image for better OCR accuracy.

        Techniques:
        1. Convert to grayscale
        2. Apply thresholding
        3. Denoise
        4. Deskew
        """
        import cv2
        import numpy as np

        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply bilateral filter to reduce noise while keeping edges
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        # Deskew if needed
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) > 100:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = 90 + angle
            if abs(angle) > 0.5:  # Only rotate if skew is significant
                (h, w) = thresh.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                thresh = cv2.warpAffine(
                    thresh, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )

        # Convert back to BGR for consistency
        result = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

        return result

    async def extract_from_pdf_images(
        self,
        pdf_path: str,
        dpi: int = 300,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract text from a scanned PDF using OCR.

        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for PDF to image conversion

        Returns:
            Tuple of (full_text, list of page results)
        """
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            import io
        except ImportError:
            raise ImportError(
                "Dependencies not installed. "
                "Install with: pip install PyMuPDF pillow"
            )

        doc = fitz.open(pdf_path)
        page_results = []
        full_text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Convert page to image
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # Save to temp file
            temp_path = f"/tmp/ocr_page_{page_num}.png"
            pix.save(temp_path)

            try:
                # Run OCR on page image
                result = await self.extract_text(temp_path)

                page_results.append({
                    'page': page_num + 1,
                    'text': result.text,
                    'confidence': result.confidence,
                    'boxes': result.boxes,
                })

                full_text_parts.append(f"[Page {page_num + 1}]\n{result.text}")

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        doc.close()

        full_text = "\n\n".join(full_text_parts)
        return full_text, page_results


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_ocr_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """Get global OCR service instance"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
