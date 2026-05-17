from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from pdf_translation.pipeline import PdfTranslationConfig, translate_pdf


def main() -> None:
    """Run an example PDF translation with explicit configuration."""
    load_dotenv()
    api_key = os.environ["PDF_TRANSLATION_API_KEY"]
    translate_pdf(
        PdfTranslationConfig(
            input_pdf_path=Path("examples/input.pdf"),
            output_pdf_path=Path("outputs/input.zh.pdf"),
            api_key=api_key,
            base_url=os.getenv("PDF_TRANSLATION_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("PDF_TRANSLATION_MODEL", "gpt-4o-mini"),
        )
    )


if __name__ == "__main__":
    main()
