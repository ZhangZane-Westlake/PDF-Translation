from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class PdfPageText:
    """Text extracted from one PDF page."""

    page_number: int
    text: str


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
            page_text = page.get_text("text").strip()
            if page_text:
                extracted_pages.append(PdfPageText(page_number=page_index, text=page_text))

    if not extracted_pages:
        raise ValueError("No extractable text found. Scanned PDFs need OCR before translation.")

    return extracted_pages
