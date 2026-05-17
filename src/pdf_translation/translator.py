from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from pdf_translation.extractor import PdfPageText

_SYSTEM_PROMPT = """你是一名专业学术翻译。请将用户提供的英文 PDF 页面内容翻译为简体中文。
要求：
1. 保留原文的段落结构和编号。
2. 专有名词、公式变量、参考文献标号保持准确。
3. 不要添加原文不存在的解释、总结或 Markdown 标记。
4. 只输出中文译文。
"""


@dataclass(frozen=True)
class TranslationClientConfig:
    """Configuration for an OpenAI-compatible translation client."""

    api_key: str
    base_url: str
    model: str
    temperature: float = 0.2


class PdfTranslationClient:
    """Client for translating extracted PDF page text into Chinese."""

    def __init__(self, config: TranslationClientConfig) -> None:
        """Initialize the translation client.

        Args:
            config: OpenAI-compatible API configuration.
        """
        self._config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    def translate_pages(self, pages: list[PdfPageText]) -> list[PdfPageText]:
        """Translate extracted PDF pages.

        Args:
            pages: Extracted English page text.

        Returns:
            Translated Chinese page text.
        """
        return [self.translate_page(page) for page in pages]

    def translate_page(self, page: PdfPageText) -> PdfPageText:
        """Translate one extracted PDF page.

        Args:
            page: Extracted English text for one page.

        Returns:
            Chinese translation for the same page number.
        """
        response = self._client.chat.completions.create(
            model=self._config.model,
            temperature=self._config.temperature,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": page.text},
            ],
        )
        translated_text = response.choices[0].message.content
        if translated_text is None:
            raise RuntimeError(f"Translation returned empty content for page {page.page_number}")
        return PdfPageText(page_number=page.page_number, text=translated_text.strip())
