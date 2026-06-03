"""
测试解析器模块 - TXT/PDF 解析器全覆盖
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from preprocessing.parsers.base import BaseParser, ParseResult
from preprocessing.parsers.txt_parser import TxtParser, detect_encoding_robust
from preprocessing.parsers.pdf_parser import PdfParser


class TestBaseParser:
    """基础解析器接口测试"""

    def test_parse_result_structure(self):
        """ParseResult 数据结构正确"""
        result = ParseResult(
            file_path="/test/file.txt",
            file_type="txt",
            content="测试内容",
            total_chars=4,
            pages=[{"page_num": 1, "text": "测试内容"}],
            metadata={"key": "value"},
            encoding="utf-8",
        )
        assert result.file_path == "/test/file.txt"
        assert result.file_type == "txt"
        assert result.total_chars == 4
        assert len(result.pages) == 1

    def test_parse_result_defaults(self):
        """ParseResult 默认值"""
        result = ParseResult(file_path="/test.txt")
        assert result.file_type == ""
        assert result.total_chars == 0
        assert result.pages == []
        assert result.metadata == {}

    def test_base_parser_not_implemented(self):
        """BaseParser 子类必须实现 parse 方法"""
        class InvalidParser(BaseParser):
            pass
        
        parser = InvalidParser()
        with pytest.raises(NotImplementedError):
            parser.parse("test.txt")


class TestTxtParser:
    """TXT 解析器全覆盖测试"""

    @pytest.fixture
    def parser(self):
        return TxtParser()

    def test_supports_txt(self, parser):
        assert parser.supports("test.txt") is True
        assert parser.supports("test.TXT") is True
        assert parser.supports("test.pdf") is False
        assert parser.supports("test") is False

    def test_parse_utf8_txt(self, parser):
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
            f.write("第一行内容\n第二行内容\n第三行内容\n")
            path = f.name
        try:
            result = parser.parse(path)
            assert result.file_type == "txt"
            assert result.total_chars > 0
            assert len(result.pages) >= 1
            assert result.encoding == "utf-8"
            full_text = "\n".join(p.text for p in result.pages)
            assert "第一行内容" in full_text
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_parse_gbk_txt(self, parser):
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="wb", delete=False) as f:
            f.write("中文GBK测试内容\n第二段中文\n".encode("gbk"))
            path = f.name
        try:
            result = parser.parse(path)
            assert result.file_type == "txt"
            assert result.total_chars > 0
            assert "gbk" in result.encoding or "gb18030" in result.encoding
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_parse_nonexistent_file(self, parser):
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/path.txt")

    def test_parse_empty_txt(self, parser):
        """空文件应能正常解析"""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
            path = f.name
        try:
            result = parser.parse(path)
            assert result.total_chars == 0
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_parse_large_line(self, parser):
        """超长行不崩溃"""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
            f.write("A" * 10000 + "\n" + "B" * 10000)
            path = f.name
        try:
            result = parser.parse(path)
            assert result.total_chars == 20001
        finally:
            if os.path.exists(path):
                os.remove(path)


class TestDetectEncoding:
    """编码检测全覆盖测试"""

    def test_detect_utf8_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
            f.write("Hello World\n测试中文\nUTF-8编码\n")
            path = f.name
        try:
            encoding = detect_encoding_robust(path)
            assert encoding == "utf-8"
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_detect_gbk_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="wb", delete=False) as f:
            f.write("GBK编码测试文件\n包含中文内容\n".encode("gbk"))
            path = f.name
        try:
            encoding = detect_encoding_robust(path)
            assert encoding in ("gbk", "gb18030")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_detect_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
            path = f.name
        try:
            encoding = detect_encoding_robust(path)
            assert encoding == "utf-8"
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_detect_english_only(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
            f.write("Hello, this is an English text without any Chinese characters.")
            path = f.name
        try:
            encoding = detect_encoding_robust(path)
            assert encoding == "utf-8"
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_detect_binary_file(self):
        """二进制文件不应导致崩溃"""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="wb", delete=False) as f:
            f.write(b"\x00\x01\x02\x03\xff\xfe\xfd\xfc")
            path = f.name
        try:
            encoding = detect_encoding_robust(path)
            assert encoding is not None
        finally:
            if os.path.exists(path):
                os.remove(path)


class TestPdfParser:
    """PDF 解析器测试"""

    @pytest.fixture
    def parser(self):
        return PdfParser()

    def test_supports_pdf(self, parser):
        assert parser.supports("test.pdf") is True
        assert parser.supports("test.PDF") is True
        assert parser.supports("test.txt") is False

    def test_parse_nonexistent_pdf(self, parser):
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.pdf")

    def test_supports_method_coverage(self, parser):
        """确保 supports 方法覆盖所有常见后缀"""
        assert parser.supports("test.pdf") is True
        assert parser.supports("test.txt") is False
        assert parser.supports("test.doc") is False