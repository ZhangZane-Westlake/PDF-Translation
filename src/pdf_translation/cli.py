from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from pdf_translation.pipeline import PdfTranslationConfig, translate_pdf

_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_DEFAULT_MODEL = "gpt-4o-mini"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns:
        Configured argument parser for the PDF translation CLI.
    """
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Translate an English PDF document into a Chinese PDF document."
    )
    parser.add_argument("input_pdf", type=Path, help="Path to the English source PDF.")
    parser.add_argument("output_pdf", type=Path, help="Path to the translated Chinese PDF.")
    parser.add_argument(
        "--api-key",
        default=os.getenv("PDF_TRANSLATION_API_KEY"),
        help="OpenAI-compatible API key. Defaults to PDF_TRANSLATION_API_KEY.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("PDF_TRANSLATION_BASE_URL", _DEFAULT_BASE_URL),
        help="OpenAI-compatible API base URL.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("PDF_TRANSLATION_MODEL", _DEFAULT_MODEL),
        help="Translation model name.",
    )
    parser.add_argument(
        "--font-path",
        type=Path,
        default=_optional_path_from_env("PDF_TRANSLATION_FONT_PATH"),
        help="Optional Chinese-capable TTF/OTF font path.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Model sampling temperature.",
    )
    return parser


def _optional_path_from_env(environment_key: str) -> Path | None:
    """Read an optional filesystem path from an environment variable.

    Args:
        environment_key: Name of the environment variable.

    Returns:
        Path value when configured, otherwise None.
    """
    environment_value = os.getenv(environment_key)
    if not environment_value:
        return None
    return Path(environment_value)


def main() -> None:
    """Run the PDF translation command-line interface."""
    parser = build_parser()
    arguments = parser.parse_args()

    if not arguments.api_key:
        parser.error("Missing API key. Set PDF_TRANSLATION_API_KEY or pass --api-key.")

    translate_pdf(
        PdfTranslationConfig(
            input_pdf_path=arguments.input_pdf,
            output_pdf_path=arguments.output_pdf,
            api_key=arguments.api_key,
            base_url=arguments.base_url,
            model=arguments.model,
            font_path=arguments.font_path,
            temperature=arguments.temperature,
        )
    )


if __name__ == "__main__":
    main()
