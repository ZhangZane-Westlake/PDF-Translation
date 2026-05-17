from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pdf_translation.extractor import extract_pdf_text
from pdf_translation.pdf_writer import write_translated_pdf
from pdf_translation.translator import PdfTranslationClient, TranslationClientConfig


@dataclass(frozen=True)
class PdfTranslationConfig:
    """Configuration for translating one English PDF into a Chinese PDF."""

    input_pdf_path: Path
    output_pdf_path: Path
    api_key: str
    base_url: str
    model: str
    font_path: Path | None = None
    temperature: float = 0.2


def translate_pdf(config: PdfTranslationConfig) -> None:
    """Translate an English PDF file into a Chinese PDF file.

    Args:
        config: Translation, input, and output configuration.
    """
    extracted_pages = extract_pdf_text(config.input_pdf_path)
    translation_client = PdfTranslationClient(
        TranslationClientConfig(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            temperature=config.temperature,
        )
    )
    translated_pages = translation_client.translate_pages(extracted_pages)
    write_translated_pdf(
        translated_pages=translated_pages,
        output_path=config.output_pdf_path,
        font_path=config.font_path,
    )
