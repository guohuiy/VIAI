"""
PDF 文件解析器
使用 PyMuPDF (fitz) 提取文本 + 字体/位置信息
"""

import os
from typing import List, Optional, Tuple
from .base import BaseParser, ParseResult, PageData, TextBlock


class PdfParser(BaseParser):
    """PDF 文件解析器（文本版）"""

    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith(".pdf")

    def parse(self, file_path: str) -> ParseResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "请安装 PyMuPDF: pip install PyMuPDF"
            )

        doc = fitz.open(file_path)
        pages = []
        total_chars = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            blocks_data = page.get_text("dict")["blocks"]

            blocks = []
            for block in blocks_data:
                if block["type"] == 0:  # 文本块
                    for line in block.get("lines", []):
                        line_text = ""
                        font_name = None
                        font_size = None
                        is_bold = False

                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                            if font_name is None:
                                font_name = span.get("font", "")
                                font_size = span.get("size", 0)
                                # 简单判断粗体
                                is_bold = "bold" in font_name.lower()

                        if line_text.strip():
                            bbox = line.get("bbox", None)
                            text_block = TextBlock(
                                text=line_text.strip(),
                                font_size=font_size,
                                font_name=font_name,
                                is_bold=is_bold,
                                bbox=bbox,
                                page_num=page_num,
                            )
                            blocks.append(text_block)

            page_data = PageData(
                text=text,
                blocks=blocks,
                page_num=page_num,
            )
            pages.append(page_data)
            total_chars += len(text)

        doc.close()

        return ParseResult(
            pages=pages,
            encoding="utf-8",
            total_chars=total_chars,
            file_path=file_path,
            file_type="pdf",
        )