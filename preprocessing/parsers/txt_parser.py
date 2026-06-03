"""
TXT 文件解析器
支持自动检测编码（UTF-8/GBK/GB2312/GB18030/Big5），
修复 chardet 误判（koi8-u/iso8859→中文编码）问题
"""

import os

from .base import BaseParser, PageData, ParseResult, TextBlock

# 常见中文编码列表（按优先级排列）
CHINESE_ENCODINGS = ["gb18030", "gbk", "gb2312", "utf-8", "big5", "utf-16"]


def detect_encoding_robust(file_path: str) -> str:
    """
    增强版编码检测
    1. 先用 chardet 检测
    2. 如果 chardet 报告非中文编码（koi8-u/iso8859），但内容有中文高位字节特征
       → 强制用中文编码尝试
    3. 用实际读取成功作为最终判定

    Args:
        file_path: 文件路径

    Returns:
        检测到的编码名称
    """
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        raw_data = f.read(min(1024 * 100, file_size))

    # 检查是否包含中文字符（高位字节 0x81-0xFE 是 GB系列编码的特征）
    has_high_bytes = any(0x81 <= raw_data[i] <= 0xFE for i in range(min(len(raw_data), 1000)))

    # 尝试用 chardet 检测（捕获可能的异常）
    try:
        import chardet
        detect_result = chardet.detect(raw_data)
        detected_enc = detect_result.get("encoding", "").lower().replace("-", "") if detect_result.get("encoding") else ""
        confidence = detect_result.get("confidence", 0)
    except Exception:
        detected_enc = ""
        confidence = 0

    # 标准化 chardet 返回的中文编码名
    enc_map = {"gb2312": "gb18030", "gbk": "gb18030", "gb18030": "gb18030",
               "utf8": "utf-8", "utf-8": "utf-8",
               "utf16": "utf-16", "utf16le": "utf-16", "utf16be": "utf-16",
               "big5": "big5", "big5hk": "big5"}
    reliable_chinese = {"gb2312", "gbk", "gb18030", "big5", "utf-8", "utf-16", "utf16le", "utf16be", "utf8", "utf16"}

    # chardet 给出可靠的中文编码 → 直接使用
    if confidence > 0.5 and detected_enc in reliable_chinese:
        return enc_map.get(detected_enc, "utf-8")

    # chardet 给出非中文编码（koi8-u/iso8859/ascii等），但内容有中文字节 → 强制中文编码
    if has_high_bytes:
        for enc in CHINESE_ENCODINGS:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    f.read(200)
                return enc  # 能成功读取就用这个编码
            except (UnicodeDecodeError, LookupError):
                continue

    # 兜底：用 chardet 结果或 utf-8
    if detected_enc and confidence > 0.1:
        mapped = enc_map.get(detected_enc)
        if mapped:
            return mapped
        # 标准化编码名
        std = detected_enc.replace("-", "").replace("_", "")
        if std in enc_map:
            return enc_map[std]
        return detected_enc

    return "utf-8"


class TxtParser(BaseParser):
    """TXT 文件解析器"""

    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith(".txt")

    def parse(self, file_path: str) -> ParseResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 增强编码检测
        encoding = detect_encoding_robust(file_path)

        # 读取内容
        content = self._read_with_fallback(file_path, encoding)

        # 按换行分段落
        paragraphs = content.split("\n")

        pages = []
        blocks = []
        page_text_parts = []
        char_count = 0
        page_size = 50  # 大约 50 段落为一页

        for i, para in enumerate(paragraphs):
            stripped = para.strip()
            if not stripped:
                continue

            block = TextBlock(
                text=stripped,
                page_num=len(pages),
            )
            blocks.append(block)
            page_text_parts.append(stripped)
            char_count += len(stripped)

            # 每 page_size 段落或最后一段时创建新页
            if (i + 1) % page_size == 0 or i == len(paragraphs) - 1:
                page = PageData(
                    text="\n".join(page_text_parts),
                    blocks=list(blocks),
                    page_num=len(pages),
                )
                pages.append(page)
                blocks = []
                page_text_parts = []

        return ParseResult(
            pages=pages,
            encoding=encoding,
            total_chars=char_count,
            file_path=file_path,
            file_type="txt",
        )

    def _read_with_fallback(self, file_path: str, preferred_encoding: str) -> str:
        """
        尝试用多种编码读取文件

        Args:
            file_path: 文件路径
            preferred_encoding: 首选编码

        Returns:
            文件内容
        """
        # 优先尝试检测到的编码，然后尝试其他常见编码
        encodings_to_try = [preferred_encoding]
        for enc in CHINESE_ENCODINGS:
            if enc not in encodings_to_try:
                encodings_to_try.append(enc)

        for enc in encodings_to_try:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue

        # 最后的降级方案：忽略错误
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
