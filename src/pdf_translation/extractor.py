from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class PdfTextBlock:
    """Text and geometry extracted from one PDF text block."""

    text: str
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class PdfPageText:
    """Text extracted from one PDF page."""

    page_number: int
    text: str
    blocks: tuple[PdfTextBlock, ...] = ()


def extract_pdf_text(pdf_path: Path) -> list[PdfPageText]:
    """Extract plain text from every page of a PDF file.

    Args:
        pdf_path: Path to the source PDF file.

    Returns:
        A list of extracted page text items in page order.

    Raises:
        FileNotFoundError: If the source PDF does not exist.
        ValueError: If no extractable text is found.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    extracted_pages: list[PdfPageText] = []
    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            text_blocks = _extract_text_blocks(page)
            page_text = "\n\n".join(block.text for block in text_blocks).strip()
            if page_text:
                extracted_pages.append(
                    PdfPageText(
                        page_number=page_index,
                        text=page_text,
                        blocks=tuple(text_blocks),
                    )
                )

    if not extracted_pages:
        raise ValueError("No extractable text found. Scanned PDFs need OCR before translation.")

    return extracted_pages


def _extract_text_blocks(page: fitz.Page) -> list[PdfTextBlock]:
    """Extract ordered text blocks and bounding boxes from one PDF page.

    Args:
        page: Source PDF page.

    Returns:
        Text blocks sorted in PDF reading order.
    """
    raw_blocks = page.get_text("blocks")
    text_blocks: list[PdfTextBlock] = []
    for raw_block in raw_blocks:
        x0, y0, x1, y1, block_text, *_ = raw_block
        cleaned_text = str(block_text).strip()
        if cleaned_text:
            text_blocks.append(
                PdfTextBlock(
                    text=cleaned_text,
                    bbox=(float(x0), float(y0), float(x1), float(y1)),
                )
            )
    return text_blocks
