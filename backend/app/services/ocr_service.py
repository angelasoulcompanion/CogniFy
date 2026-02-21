"""
CogniFy OCR Service
Typhoon-OCR 1.5-3B via Ollama Vision API — bilingual Thai+English document parsing
Created with love by Angela & David - 1 January 2026
Upgraded to Typhoon-OCR - 21 February 2026
"""

import os
import base64
import tempfile
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.logging import logger

OCR_PROMPT = (
    "Extract ALL text from this document image. "
    "Preserve the original structure (headings, paragraphs, lists, tables). "
    "Support both Thai and English text. "
    "Output only the extracted text, no explanations."
)


@dataclass
class OCRResult:
    """OCR extraction result"""
    text: str
    confidence: float
    language: str
    engine: str


class OCRService:
    """
    OCR Service using Typhoon-OCR 1.5-3B via Ollama Vision API.

    Primary: scb10x/typhoon-ocr1.5-3b (bilingual Thai+English, 125K context)
    Fallback: Tesseract (if Typhoon-OCR fails)
    """

    def __init__(self):
        self.model = settings.OCR_MODEL
        self.ollama_url = settings.OLLAMA_BASE_URL

    async def extract_text(self, image_path: str) -> OCRResult:
        """
        Extract text from an image file using Typhoon-OCR via Ollama.

        Args:
            image_path: Path to the image file

        Returns:
            OCRResult with extracted text and metadata
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Try Typhoon-OCR first, fallback to Tesseract
        try:
            return await self._extract_with_typhoon(image_path)
        except Exception as e:
            logger.warning(f"Typhoon-OCR failed: {e}, falling back to Tesseract")
            try:
                return await self._extract_with_tesseract(image_path)
            except Exception as te:
                logger.error(f"Tesseract fallback also failed: {te}")
                raise RuntimeError(
                    f"All OCR engines failed. Typhoon-OCR: {e}, Tesseract: {te}"
                )

    async def _extract_with_typhoon(self, image_path: str) -> OCRResult:
        """Extract text using Typhoon-OCR 1.5-3B via Ollama Vision API"""
        # Read and base64 encode the image
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Call Ollama vision API
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": OCR_PROMPT,
                            "images": [image_b64],
                        }
                    ],
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
            )
            response.raise_for_status()
            data = response.json()

        text = data.get("message", {}).get("content", "").strip()

        if not text:
            raise ValueError("Typhoon-OCR returned empty text")

        return OCRResult(
            text=text,
            confidence=0.95,  # Typhoon-OCR is high quality for Thai+English
            language="th+en",
            engine="typhoon-ocr",
        )

    async def _extract_with_tesseract(self, image_path: str) -> OCRResult:
        """Fallback: extract text using Tesseract OCR"""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            raise ImportError(
                "Tesseract fallback not available. "
                "Install with: pip install pytesseract pillow"
            )

        img = Image.open(image_path)

        try:
            text = pytesseract.image_to_string(
                img,
                lang="tha+eng",
                config="--psm 6 --oem 3",
            )
        except pytesseract.TesseractNotFoundError:
            raise ImportError(
                "Tesseract not found. Install with: brew install tesseract tesseract-lang"
            )

        return OCRResult(
            text=text.strip(),
            confidence=0.7,
            language="th+en",
            engine="tesseract",
        )

    async def extract_from_pdf_images(
        self,
        pdf_path: str,
        dpi: int = 300,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract text from a scanned PDF using OCR on each page.

        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for PDF to image conversion

        Returns:
            Tuple of (full_text, list of page results)
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF not installed. Install with: pip install PyMuPDF")

        doc = fitz.open(pdf_path)
        page_results = []
        full_text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            logger.debug("OCR page {}/{}", page_num + 1, len(doc))

            # Render page to image
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                temp_path = tmp.name
                pix.save(temp_path)

            try:
                result = await self.extract_text(temp_path)

                page_results.append({
                    "page": page_num + 1,
                    "text": result.text,
                    "confidence": result.confidence,
                    "engine": result.engine,
                })

                full_text_parts.append(f"[Page {page_num + 1}]\n{result.text}")

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        doc.close()

        full_text = "\n\n".join(full_text_parts)
        return full_text, page_results


# =============================================================================
# SINGLETON ACCESS (delegates to ServiceContainer)
# =============================================================================

def get_ocr_service() -> OCRService:
    """Get OCRService via the global ServiceContainer"""
    from app.core.container import get_container
    return get_container().ocr
