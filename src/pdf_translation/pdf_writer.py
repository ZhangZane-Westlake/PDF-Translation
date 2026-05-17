from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate

from pdf_translation.extractor import PdfPageText

_DEFAULT_FONT_NAME = "STSong-Light"
_CUSTOM_FONT_NAME = "PdfTranslationCjkFont"


def register_chinese_font(font_path: Path | None) -> str:
    """Register a Chinese-capable font for PDF generation.

    Args:
        font_path: Optional path to a TrueType/OpenType font file.

    Returns:
        The registered ReportLab font name.
    """
    if font_path is not None:
        if not font_path.exists():
            raise FileNotFoundError(f"Font file not found: {font_path}")
        pdfmetrics.registerFont(TTFont(_CUSTOM_FONT_NAME, str(font_path)))
        return _CUSTOM_FONT_NAME

    pdfmetrics.registerFont(UnicodeCIDFont(_DEFAULT_FONT_NAME))
    return _DEFAULT_FONT_NAME


def write_translated_pdf(
    translated_pages: list[PdfPageText],
    output_path: Path,
    font_path: Path | None = None,
) -> None:
    """Write translated Chinese page text into a PDF file.

    Args:
        translated_pages: Translated page text in page order.
        output_path: Path where the translated PDF will be written.
        font_path: Optional path to a Chinese-capable font file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font_name = register_chinese_font(font_path)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ChineseTitle",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=14,
        leading=20,
        spaceAfter=6 * mm,
    )
    body_style = ParagraphStyle(
        "ChineseBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10.5,
        leading=16,
        firstLineIndent=7 * mm,
        spaceAfter=3 * mm,
    )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    story: list[Flowable] = []

    for page_index, page_text in enumerate(translated_pages):
        story.append(Paragraph(f"第 {page_text.page_number} 页译文", title_style))
        for paragraph in page_text.text.split("\n"):
            cleaned_paragraph = paragraph.strip()
            if cleaned_paragraph:
                story.append(Paragraph(cleaned_paragraph.replace("\n", "<br />"), body_style))
        if page_index < len(translated_pages) - 1:
            story.append(PageBreak())

    document.build(story)


def write_bilingual_pdf(
    source_pdf_path: Path,
    translated_pages: list[PdfPageText],
    output_path: Path,
    font_path: Path | None = None,
) -> None:
    """Write a bilingual PDF that preserves original pages and appends translations.

    Args:
        source_pdf_path: Path to the original PDF file.
        translated_pages: Translated page text in page order.
        output_path: Path where the bilingual PDF will be written.
        font_path: Optional path to a Chinese-capable font file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    translated_pages_by_number = {page.page_number: page for page in translated_pages}

    with fitz.open(source_pdf_path) as source_document:
        with fitz.open() as output_document:
            for source_page_index in range(source_document.page_count):
                output_document.insert_pdf(
                    source_document,
                    from_page=source_page_index,
                    to_page=source_page_index,
                )
                source_page_number = source_page_index + 1
                translated_page = translated_pages_by_number.get(source_page_number)
                if translated_page is not None:
                    _insert_translation_pages(
                        output_document=output_document,
                        translated_page=translated_page,
                        font_path=font_path,
                    )
            output_document.save(output_path)


def _insert_translation_pages(
    output_document: fitz.Document,
    translated_page: PdfPageText,
    font_path: Path | None,
) -> None:
    """Insert all generated translation pages for one source page.

    Args:
        output_document: Output PDF document being assembled.
        translated_page: Translated text for one source page.
        font_path: Optional path to a Chinese-capable font file.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temporary_file:
        translated_pdf_path = Path(temporary_file.name)

    try:
        write_translated_pdf([translated_page], translated_pdf_path, font_path)
        with fitz.open(translated_pdf_path) as translated_document:
            output_document.insert_pdf(translated_document)
    finally:
        translated_pdf_path.unlink(missing_ok=True)


def write_overlay_pdf(
    source_pdf_path: Path,
    translated_pages: list[PdfPageText],
    output_path: Path,
    font_path: Path | None = None,
) -> None:
    """Write a PDF that attempts to replace original text blocks in place.

    Args:
        source_pdf_path: Path to the original PDF file.
        translated_pages: Translated page text with original text block geometry.
        output_path: Path where the overlay PDF will be written.
        font_path: Optional path to a Chinese-capable font file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if font_path is None:
        raise ValueError("overlay mode requires --font-path with a Chinese-capable TTF/OTF font")
    font_file = _resolve_overlay_font_file(font_path)
    translated_pages_by_number = {page.page_number: page for page in translated_pages}

    with fitz.open(source_pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            translated_page = translated_pages_by_number.get(page_index)
            if translated_page is None:
                continue
            _overlay_translation_on_page(page, translated_page, font_file)
        document.save(output_path)


def _overlay_translation_on_page(
    page: fitz.Page,
    translated_page: PdfPageText,
    font_file: str | None,
) -> None:
    """Overlay translated text over original text blocks on one page.

    Args:
        page: PDF page to modify.
        translated_page: Translated text and source text block geometry.
        font_file: Optional Chinese-capable font file for PyMuPDF insertion.
    """
    translated_chunks = _split_translation_for_blocks(translated_page)
    for block, translated_text in zip(translated_page.blocks, translated_chunks, strict=False):
        rectangle = fitz.Rect(block.bbox)
        page.draw_rect(rectangle, color=None, fill=(1, 1, 1), overlay=True)
        page.insert_textbox(
            rectangle,
            translated_text,
            fontsize=_estimate_overlay_font_size(rectangle),
            fontname="cjk",
            fontfile=font_file,
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT,
            overlay=True,
        )


def _resolve_overlay_font_file(font_path: Path | None) -> str | None:
    """Resolve an optional font file for PyMuPDF overlay text insertion.

    Args:
        font_path: Optional path to a Chinese-capable font file.

    Returns:
        String path for PyMuPDF when configured, otherwise None.
    """
    if font_path is None:
        return None
    if not font_path.exists():
        raise FileNotFoundError(f"Font file not found: {font_path}")
    return str(font_path)


def _split_translation_for_blocks(translated_page: PdfPageText) -> list[str]:
    """Split translated page text into chunks for source text blocks.

    Args:
        translated_page: Translated page text with source block metadata.

    Returns:
        Translation chunks aligned approximately to source text blocks.
    """
    paragraphs = [paragraph.strip() for paragraph in translated_page.text.split("\n\n") if paragraph.strip()]
    if len(paragraphs) >= len(translated_page.blocks):
        return paragraphs[: len(translated_page.blocks)]
    if not translated_page.blocks:
        return []
    return _split_text_evenly(translated_page.text, len(translated_page.blocks))


def _split_text_evenly(text: str, chunk_count: int) -> list[str]:
    """Split text into approximately equal chunks.

    Args:
        text: Text to split.
        chunk_count: Number of chunks to return.

    Returns:
        Approximately equal text chunks.
    """
    if chunk_count <= 1:
        return [text]
    chunk_size = max(1, len(text) // chunk_count)
    chunks = [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]
    if len(chunks) < chunk_count:
        chunks.extend("" for _ in range(chunk_count - len(chunks)))
    return chunks[:chunk_count]


def _estimate_overlay_font_size(rectangle: fitz.Rect) -> float:
    """Estimate a readable font size for one text block rectangle.

    Args:
        rectangle: Target text block rectangle.

    Returns:
        Font size in PDF points.
    """
    return max(5.0, min(9.5, rectangle.height / 5.0))
