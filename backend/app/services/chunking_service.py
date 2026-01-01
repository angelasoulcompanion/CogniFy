"""
CogniFy Chunking Service
Semantic text chunking with overlap for RAG
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class Chunk:
    """Represents a text chunk with metadata"""
    content: str
    index: int
    start_char: int
    end_char: int
    token_count: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None


class ChunkingService:
    """
    Service for splitting documents into semantic chunks.

    Features:
    - Configurable chunk size and overlap
    - Sentence-aware splitting (doesn't break sentences)
    - Thai language support
    - Page number tracking
    - Section title extraction
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP
        self.min_chunk_size = min_chunk_size

        # Sentence delimiters for Thai and English
        self.sentence_delimiters = r'[.!?।॥。！？\n]+'
        self.thai_sentence_pattern = re.compile(r'[\u0E00-\u0E7F]+[.!?\n]+|[.!?\n]+')

    def _count_tokens(self, text: str) -> int:
        """
        Approximate token count.
        For more accurate counting, use tiktoken.
        """
        # Simple approximation: words + Thai characters / 2
        words = len(text.split())
        thai_chars = len(re.findall(r'[\u0E00-\u0E7F]', text))
        return words + (thai_chars // 2)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences, handling Thai and English"""
        # Replace multiple newlines with single marker
        text = re.sub(r'\n{2,}', '\n\n', text)

        # Split by sentence delimiters while keeping the delimiter
        sentences = re.split(r'(?<=[.!?।॥。！？\n])\s*', text)

        # Clean up and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _extract_section_title(self, text: str) -> Optional[str]:
        """Extract section title if text starts with a heading pattern"""
        lines = text.strip().split('\n')
        if not lines:
            return None

        first_line = lines[0].strip()

        # Check for common heading patterns
        # Markdown headers
        if first_line.startswith('#'):
            return first_line.lstrip('#').strip()

        # Numbered sections (1. Title, 1.1 Title)
        match = re.match(r'^(\d+\.?\d*\.?\s*)(.+)$', first_line)
        if match and len(first_line) < 100:
            return match.group(2).strip()

        # ALL CAPS titles
        if first_line.isupper() and len(first_line) < 100:
            return first_line

        # Short first line followed by longer text (likely a title)
        if len(first_line) < 80 and len(lines) > 1:
            second_line = lines[1].strip() if len(lines) > 1 else ""
            if len(second_line) > len(first_line):
                return first_line

        return None

    def chunk_text(
        self,
        text: str,
        page_numbers: Optional[List[Tuple[int, int]]] = None
    ) -> List[Chunk]:
        """
        Split text into chunks with overlap.

        Args:
            text: The text to chunk
            page_numbers: Optional list of (start_char, page_number) tuples

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        # Split into sentences
        sentences = self._split_sentences(text)

        if not sentences:
            return []

        chunks: List[Chunk] = []
        current_chunk_sentences: List[str] = []
        current_token_count = 0
        chunk_start_char = 0
        current_char_pos = 0

        for i, sentence in enumerate(sentences):
            sentence_tokens = self._count_tokens(sentence)

            # Check if adding this sentence would exceed chunk size
            if current_token_count + sentence_tokens > self.chunk_size and current_chunk_sentences:
                # Create chunk from current sentences
                chunk_text = ' '.join(current_chunk_sentences)
                chunk_end_char = current_char_pos

                # Determine page number
                page_num = None
                if page_numbers:
                    for start, page in reversed(page_numbers):
                        if start <= chunk_start_char:
                            page_num = page
                            break

                # Extract section title
                section_title = self._extract_section_title(chunk_text)

                chunks.append(Chunk(
                    content=chunk_text,
                    index=len(chunks),
                    start_char=chunk_start_char,
                    end_char=chunk_end_char,
                    token_count=current_token_count,
                    page_number=page_num,
                    section_title=section_title,
                ))

                # Calculate overlap - keep last N tokens worth of sentences
                overlap_sentences: List[str] = []
                overlap_tokens = 0
                for s in reversed(current_chunk_sentences):
                    s_tokens = self._count_tokens(s)
                    if overlap_tokens + s_tokens <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_tokens += s_tokens
                    else:
                        break

                # Start new chunk with overlap
                current_chunk_sentences = overlap_sentences.copy()
                current_token_count = overlap_tokens
                chunk_start_char = chunk_end_char - len(' '.join(overlap_sentences))

            # Add sentence to current chunk
            current_chunk_sentences.append(sentence)
            current_token_count += sentence_tokens
            current_char_pos += len(sentence) + 1  # +1 for space

        # Don't forget the last chunk
        if current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)

            # Only add if meets minimum size
            if self._count_tokens(chunk_text) >= self.min_chunk_size or not chunks:
                page_num = None
                if page_numbers:
                    for start, page in reversed(page_numbers):
                        if start <= chunk_start_char:
                            page_num = page
                            break

                section_title = self._extract_section_title(chunk_text)

                chunks.append(Chunk(
                    content=chunk_text,
                    index=len(chunks),
                    start_char=chunk_start_char,
                    end_char=current_char_pos,
                    token_count=current_token_count,
                    page_number=page_num,
                    section_title=section_title,
                ))

        return chunks

    def chunk_by_pages(
        self,
        pages: List[Tuple[int, str]]
    ) -> List[Chunk]:
        """
        Chunk text while preserving page information.

        Args:
            pages: List of (page_number, page_text) tuples

        Returns:
            List of Chunk objects with page numbers
        """
        # Combine all pages with page markers
        combined_text = ""
        page_markers: List[Tuple[int, int]] = []  # (start_char, page_number)

        for page_num, page_text in pages:
            page_markers.append((len(combined_text), page_num))
            combined_text += page_text + "\n\n"

        return self.chunk_text(combined_text, page_markers)

    def rechunk_if_needed(
        self,
        chunks: List[Chunk],
        max_tokens: int = None
    ) -> List[Chunk]:
        """
        Re-chunk if any chunk exceeds max_tokens.
        Useful for ensuring chunks fit in LLM context.
        """
        max_tokens = max_tokens or self.chunk_size * 2

        result: List[Chunk] = []

        for chunk in chunks:
            if chunk.token_count <= max_tokens:
                chunk.index = len(result)
                result.append(chunk)
            else:
                # Re-chunk this oversized chunk
                sub_chunks = self.chunk_text(chunk.content)
                for sub_chunk in sub_chunks:
                    sub_chunk.index = len(result)
                    sub_chunk.page_number = chunk.page_number
                    result.append(sub_chunk)

        return result


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_chunking_service: Optional[ChunkingService] = None


def get_chunking_service() -> ChunkingService:
    """Get global ChunkingService instance"""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
