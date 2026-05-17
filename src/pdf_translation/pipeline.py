from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pdf_translation.extractor import extract_pdf_text
from pdf_translation.pdf_writer import (
    write_bilingual_pdf,
    write_overlay_pdf,
    write_translated_pdf,
)
from pdf_translation.translator import PdfTranslationClient, TranslationClientConfig

ProgressCallback = Callable[[str], None]
OutputMode = Literal["translation-only", "bilingual", "overlay"]


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
    output_mode: OutputMode = "bilingual"
    max_workers: int = 1


def translate_pdf(
    config: PdfTranslationConfig,
    progress_callback: ProgressCallback | None = None,
) -> None:
    """Translate an English PDF file into a Chinese PDF file.

    Args:
        config: Translation, input, and output configuration.
        progress_callback: Optional callback for safe progress messages.
    """
    _report_progress(progress_callback, f"Extracting text from {config.input_pdf_path}")
    extracted_pages = extract_pdf_text(config.input_pdf_path)
    _report_progress(progress_callback, f"Extracted text from {len(extracted_pages)} page(s)")
    _report_progress(progress_callback, f"Using model {config.model} at {config.base_url}")

    translation_client = PdfTranslationClient(
        TranslationClientConfig(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            temperature=config.temperature,
            max_workers=config.max_workers,
        ),
        progress_callback=progress_callback,
    )
    translated_pages = translation_client.translate_pages(extracted_pages)
    _report_progress(progress_callback, f"Writing translated PDF to {config.output_pdf_path}")
    if config.output_mode == "bilingual":
        write_bilingual_pdf(
            source_pdf_path=config.input_pdf_path,
            translated_pages=translated_pages,
            output_path=config.output_pdf_path,
            font_path=config.font_path,
        )
    elif config.output_mode == "overlay":
        write_overlay_pdf(
            source_pdf_path=config.input_pdf_path,
            translated_pages=translated_pages,
            output_path=config.output_pdf_path,
            font_path=config.font_path,
        )
    else:
        write_translated_pdf(
            translated_pages=translated_pages,
            output_path=config.output_pdf_path,
            font_path=config.font_path,
        )
    _report_progress(progress_callback, "Done")


def _report_progress(
    progress_callback: ProgressCallback | None,
    message: str,
) -> None:
    """Report a progress message when a callback is configured.

    Args:
        progress_callback: Optional callback for safe progress messages.
        message: Safe progress message without secrets.
    """
    if progress_callback is not None:
        progress_callback(message)
