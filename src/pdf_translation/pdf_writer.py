from __future__ import annotations

from pathlib import Path

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
        story.append(Paragraph(f"第 {page_text.page_number} 页", title_style))
        for paragraph in page_text.text.split("\n"):
            cleaned_paragraph = paragraph.strip()
            if cleaned_paragraph:
                story.append(Paragraph(cleaned_paragraph.replace("\n", "<br />"), body_style))
        if page_index < len(translated_pages) - 1:
            story.append(PageBreak())

    document.build(story)
