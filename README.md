# PDF-Translation

将指定英文 PDF 文档翻译为中文 PDF 的 Python 项目。项目会从可复制文本型 PDF 中提取英文内容，调用 OpenAI 兼容接口完成翻译，再生成包含中文译文的新 PDF。

## 功能

- 提取英文 PDF 每页文本。
- 调用 OpenAI 兼容 Chat Completions API 翻译为简体中文。
- 按页生成中文 PDF，保留页码与段落结构。
- 支持 `.env` 配置 API key、base URL、模型和中文字体。
- 提供命令行入口 `pdf-translate` 和 Python API。

## 适用范围

本项目适用于文本型 PDF。如果源文件是扫描版图片 PDF，需要先使用 OCR 工具生成可复制文本后再翻译。

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

也可以仅安装依赖：

```bash
pip install -r requirements.txt
```

## 配置

复制示例环境变量文件：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
PDF_TRANSLATION_API_KEY=your-api-key
PDF_TRANSLATION_BASE_URL=https://api.openai.com/v1
PDF_TRANSLATION_MODEL=gpt-4o-mini
PDF_TRANSLATION_FONT_PATH=
```

说明：

- `PDF_TRANSLATION_API_KEY`：必填，OpenAI 兼容接口密钥。
- `PDF_TRANSLATION_BASE_URL`：可选，默认 `https://api.openai.com/v1`。
- `PDF_TRANSLATION_MODEL`：可选，默认 `gpt-4o-mini`。
- `PDF_TRANSLATION_FONT_PATH`：可选，中文 TTF/OTF 字体路径；未设置时使用 ReportLab 内置中文 CID 字体。

## 命令行使用

```bash
pdf-translate input.pdf outputs/input.zh.pdf
```

也可以通过命令行覆盖配置：

```bash
pdf-translate input.pdf outputs/input.zh.pdf \
  --base-url https://api.openai.com/v1 \
  --model gpt-4o-mini \
  --font-path /path/to/chinese-font.ttf
```

## Python API 使用

```python
import os
from pathlib import Path

from dotenv import load_dotenv

from pdf_translation.pipeline import PdfTranslationConfig, translate_pdf

load_dotenv()

translate_pdf(
    PdfTranslationConfig(
        input_pdf_path=Path("input.pdf"),
        output_pdf_path=Path("outputs/input.zh.pdf"),
        api_key=os.environ["PDF_TRANSLATION_API_KEY"],
        base_url=os.getenv("PDF_TRANSLATION_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("PDF_TRANSLATION_MODEL", "gpt-4o-mini"),
    )
)
```

推荐参考 `examples/translate_example.py`，实际项目中不要在代码里硬编码 API key。

## 项目结构

```text
.
├── examples/
│   └── translate_example.py
├── src/
│   └── pdf_translation/
│       ├── __init__.py
│       ├── cli.py
│       ├── extractor.py
│       ├── pdf_writer.py
│       ├── pipeline.py
│       └── translator.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 注意事项

- PDF 排版重建是重新生成译文 PDF，不会复刻原 PDF 的复杂版式、图片、表格和公式位置。
- 长 PDF 会逐页调用模型接口，成本与耗时取决于页数和文本量。
- 如果翻译质量不符合预期，可以更换模型或调整 `--temperature`。
