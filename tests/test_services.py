"""
测试服务层 - BookService 和 GenerationService
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest


class TestBookService:
    """BookService 测试"""

    @pytest.fixture
    def service(self):
        from services.book_service import BookService
        return BookService()

    def test_compute_file_hash(self):
        """文件哈希计算验证"""
        from services.book_service import compute_file_hash

        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write("test content")
            path = f.name
        try:
            hash_val = compute_file_hash(path)
            assert isinstance(hash_val, str)
            assert len(hash_val) == 32  # MD5
        finally:
            os.remove(path)

    def test_compute_file_hash_nonexistent(self):
        from services.book_service import compute_file_hash
        assert compute_file_hash("/nonexistent") == ""

    def test_infer_category_from_path(self):
        from services.book_service import infer_category_from_path
        cat = infer_category_from_path("/data/历史军事/test.txt")
        assert cat == "历史军事"

    def test_infer_category_from_path_no_category(self):
        from services.book_service import infer_category_from_path
        cat = infer_category_from_path("/data/test.txt")
        assert isinstance(cat, str)

    def test_list_books_empty(self, service):
        books = service.list_books()
        assert isinstance(books, list)

    def test_list_books_structure(self, service):
        books = service.list_books()
        if books:
            book = books[0]
            assert "id" in book
            assert "title" in book


class TestGenerationService:
    """GenerationService 测试"""

    def test_initialization(self):
        from services.generation_service import GenerationService
        service = GenerationService()
        assert service is not None