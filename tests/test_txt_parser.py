"""
测试 TXT 解析器模块
"""

import os
import tempfile

import pytest

from preprocessing.parsers.txt_parser import TxtParser, detect_encoding_robust


class TestTxtParser:
    """TXT 解析器功能测试"""

    @pytest.fixture
    def parser(self):
        return TxtParser()

    @pytest.fixture
    def temp_txt_file(self):
        """创建临时 UTF-8 TXT 文件"""
        content = "第一行内容\n第二行内容\n第三行内容\n"
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8")
        tmp.write(content)
        path = tmp.name
        tmp.close()
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def temp_gbk_file(self):
        """创建临时 GBK TXT 文件"""
        content = "中文GBK测试内容\n第二段中文\n"
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb")
        tmp.write(content.encode("gbk"))
        path = tmp.name
        tmp.close()
        yield path
        if os.path.exists(path):
            os.remove(path)

    def test_supports_txt(self, parser):
        assert parser.supports("test.txt") is True
        assert parser.supports("test.TXT") is True
        assert parser.supports("test.pdf") is False
        assert parser.supports("test") is False

    def test_parse_utf8_txt(self, parser, temp_txt_file):
        result = parser.parse(temp_txt_file)
        assert result.file_type == "txt"
        assert result.total_chars > 0
        assert len(result.pages) >= 1
        assert result.encoding == "utf-8"
        # 应该能拼接出完整的文本
        full_text = "\n".join(p.text for p in result.pages)
        assert "第一行内容" in full_text

    def test_parse_gbk_txt(self, parser, temp_gbk_file):
        result = parser.parse(temp_gbk_file)
        assert result.file_type == "txt"
        assert result.total_chars > 0
        # 自动检测为中文编码
        assert "gbk" in result.encoding or "gb18030" in result.encoding
        full_text = "\n".join(p.text for p in result.pages)
        assert "中文GBK测试内容" in full_text

    def test_parse_nonexistent_file(self, parser):
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/path.txt")


class TestDetectEncoding:
    """编码检测功能测试"""

    @pytest.fixture
    def utf8_file(self):
        content = "Hello World\n测试中文\nUTF-8编码\n"
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8")
        tmp.write(content)
        path = tmp.name
        tmp.close()
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def gbk_file(self):
        content = "GBK编码测试文件\n包含中文内容\n"
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb")
        tmp.write(content.encode("gbk"))
        path = tmp.name
        tmp.close()
        yield path
        if os.path.exists(path):
            os.remove(path)

    def test_detect_utf8(self, utf8_file):
        encoding = detect_encoding_robust(utf8_file)
        assert encoding == "utf-8"

    def test_detect_gbk(self, gbk_file):
        encoding = detect_encoding_robust(gbk_file)
        assert encoding in ("gbk", "gb18030")

    def test_detect_empty_file(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8")
        path = tmp.name
        tmp.close()
        try:
            encoding = detect_encoding_robust(path)
            assert encoding == "utf-8"
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_detect_english_only(self):
        content = "Hello, this is an English text without any Chinese characters."
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8")
        tmp.write(content)
        path = tmp.name
        tmp.close()
        try:
            encoding = detect_encoding_robust(path)
            assert encoding == "utf-8"
        finally:
            if os.path.exists(path):
                os.remove(path)
