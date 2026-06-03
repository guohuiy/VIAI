"""
测试数据库模块 (SQLite in-memory 模式)
"""

import os
import tempfile

import pytest

from storage.db import DatabaseManager


@pytest.fixture
def db_with_schema():
    """创建临时数据库并初始化 schema"""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()

    # 写入最小 schema
    schema_sql = """
    CREATE TABLE IF NOT EXISTS books (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL DEFAULT '',
        author TEXT DEFAULT '',
        file_path TEXT DEFAULT '',
        category TEXT DEFAULT '',
        file_hash TEXT DEFAULT '',
        language TEXT DEFAULT '中文',
        summary TEXT DEFAULT '',
        total_chars INTEGER DEFAULT 0,
        total_chunks INTEGER DEFAULT 0,
        embedding_model TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        book_id TEXT NOT NULL,
        content TEXT NOT NULL,
        struct_path TEXT DEFAULT '',
        start_char INTEGER DEFAULT 0,
        end_char INTEGER DEFAULT 0,
        heading_stack TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS chapters (
        id TEXT PRIMARY KEY,
        book_id TEXT NOT NULL,
        parent_id TEXT DEFAULT '',
        level INTEGER DEFAULT 0,
        title TEXT DEFAULT '',
        start_char INTEGER DEFAULT 0,
        end_char INTEGER DEFAULT 0,
        summary TEXT DEFAULT '',
        chunk_ids TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS chunk_tags (
        chunk_id TEXT NOT NULL,
        tag TEXT NOT NULL,
        PRIMARY KEY (chunk_id, tag)
    );
    CREATE TABLE IF NOT EXISTS fts_chunks (
        chunk_id TEXT PRIMARY KEY,
        content TEXT NOT NULL
    );
    """
    # 写入 schema.sql 供 DatabaseManager._init_db 读取
    schema_dir = os.path.join(os.path.dirname(__file__), "..", "storage")
    os.makedirs(schema_dir, exist_ok=True)
    schema_path = os.path.join(schema_dir, "schema.sql")
    with open(schema_path, "w", encoding="utf-8") as f:
        f.write(schema_sql)

    # 注入测试 db_path
    original_sqlite = None
    import storage.db as db_module
    original_sqlite = db_module.STORAGE_CONFIG["sqlite"]
    db_module.STORAGE_CONFIG["sqlite"] = db_path

    mgr = DatabaseManager(db_path=db_path)
    yield mgr

    mgr.close()
    db_module.STORAGE_CONFIG["sqlite"] = original_sqlite
    if os.path.exists(schema_path):
        os.remove(schema_path)
    if os.path.exists(db_path):
        os.remove(db_path)
    # 清理 wal 文件
    for ext in ("-wal", "-shm"):
        p = db_path + ext
        if os.path.exists(p):
            os.remove(p)


class TestDatabaseManager:
    """数据库管理器 CRUD 测试"""

    def test_add_and_get_book(self, db_with_schema):
        db = db_with_schema
        book = {
            "id": "test-001",
            "title": "测试书籍",
            "author": "测试作者",
            "file_path": "/tmp/test.txt",
            "category": "技术",
            "file_hash": "abc123",
            "language": "中文",
            "summary": "这是一本测试书",
            "total_chars": 1000,
            "total_chunks": 5,
            "embedding_model": "bge-m3",
        }
        db.add_book(book)
        result = db.get_book("test-001")
        assert result is not None
        assert result["title"] == "测试书籍"
        assert result["category"] == "技术"

    def test_get_all_books(self, db_with_schema):
        db = db_with_schema
        books = [
            {"id": f"b{i:03d}", "title": f"Book {i}", "author": "Author",
             "file_path": "", "category": "cat", "file_hash": "",
             "language": "中文", "summary": "", "total_chars": 100,
             "total_chunks": 1, "embedding_model": "bge-m3"}
            for i in range(3)
        ]
        for b in books:
            db.add_book(b)
        all_books = db.get_all_books()
        assert len(all_books) == 3

    def test_delete_book_cascade(self, db_with_schema):
        db = db_with_schema
        book = {
            "id": "del-test", "title": "待删除", "author": "",
            "file_path": "", "category": "", "file_hash": "",
            "language": "中文", "summary": "", "total_chars": 0,
            "total_chunks": 0, "embedding_model": "",
        }
        db.add_book(book)
        db.add_chunk({
            "chunk_id": "chunk-del", "book_id": "del-test",
            "content": "测试内容", "struct_path": "",
            "start_char": 0, "end_char": 4, "heading_stack": "",
        })
        db.delete_book("del-test")
        assert db.get_book("del-test") is None

    def test_add_chunks_batch(self, db_with_schema):
        db = db_with_schema
        chunks = [
            {"chunk_id": f"c{i:03d}", "book_id": "batch-test",
             "content": f"Content {i}", "struct_path": "",
             "start_char": i * 10, "end_char": (i + 1) * 10,
             "heading_stack": ""}
            for i in range(5)
        ]
        db.add_chunks_batch(chunks)
        result = db.get_chunks_by_book("batch-test")
        assert len(result) == 5

    def test_get_nonexistent_book(self, db_with_schema):
        assert db_with_schema.get_book("nonexistent") is None

    def test_add_chunk_tags(self, db_with_schema):
        db = db_with_schema
        db.add_chunk({
            "chunk_id": "tag-test", "book_id": "b1",
            "content": "tag content", "struct_path": "",
            "start_char": 0, "end_char": 11, "heading_stack": "",
        })
        db.add_chunk_tags("tag-test", ["python", "test", "ci"])
        results = db.get_chunks_by_tag("python")
        assert len(results) == 1
        assert results[0]["chunk_id"] == "tag-test"
