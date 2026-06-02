"""
测试全文检索引擎
"""

import os
import tempfile
import pytest
from retrieval.fulltext_engine import FullTextEngine


@pytest.fixture
def fts_tmp_db():
    """创建临时 SQLite 数据库供全文检索测试"""
    # 先确保 schema 文件存在
    schema_sql = """
    CREATE TABLE IF NOT EXISTS books (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL DEFAULT ''
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
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
        chunk_id UNINDEXED, content
    );
    """
    from pathlib import Path
    schema_dir = Path(__file__).resolve().parent.parent / "storage"
    schema_dir.mkdir(exist_ok=True)
    schema_path = schema_dir / "schema.sql"
    with open(schema_path, "w", encoding="utf-8") as f:
        f.write(schema_sql)

    # 创建临时数据库
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()

    # 初始化表结构
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql)

    # 插入示例数据
    conn.execute("INSERT INTO books (id, title) VALUES ('b1', '测试书籍')")
    conn.execute(
        "INSERT INTO chunks (chunk_id, book_id, content) VALUES ('c1', 'b1', 'Python机器学习入门')"
    )
    conn.execute(
        "INSERT INTO chunks (chunk_id, book_id, content) VALUES ('c2', 'b1', '深度学习与神经网络')"
    )
    conn.execute(
        "INSERT INTO chunks (chunk_id, book_id, content) VALUES ('c3', 'b1', '数据统计分析基础')"
    )
    # 添加到 fts
    conn.execute("INSERT INTO fts_chunks (chunk_id, content) VALUES ('c1', 'Python机器学习入门')")
    conn.execute("INSERT INTO fts_chunks (chunk_id, content) VALUES ('c2', '深度学习与神经网络')")
    conn.execute("INSERT INTO fts_chunks (chunk_id, content) VALUES ('c3', '数据统计分析基础')")
    conn.commit()
    conn.close()

    engine = FullTextEngine(db_path=db_path)
    yield engine
    engine.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    for ext in ("-wal", "-shm"):
        p = db_path + ext
        if os.path.exists(p):
            os.remove(p)
    # 清理临时 schema
    if schema_path.exists():
        schema_path.unlink()


class TestFullTextEngine:
    """全文检索引擎测试"""

    def test_search_found(self, fts_tmp_db):
        results = fts_tmp_db.search("Python")
        assert len(results) >= 1
        assert any("Python" in r["content"] for r in results)

    def test_search_not_found(self, fts_tmp_db):
        results = fts_tmp_db.search("NonExistentWordXYZ")
        assert len(results) == 0

    def test_search_multiple_terms(self, fts_tmp_db):
        results = fts_tmp_db.search("机器学习")
        assert len(results) >= 1

    def test_search_top_k(self, fts_tmp_db):
        results = fts_tmp_db.search("学习", top_k=1)
        assert len(results) <= 1

    def test_add_document(self, fts_tmp_db):
        fts_tmp_db.add_document("c4", "新增测试文档内容")
        results = fts_tmp_db.search("新增")
        assert len(results) >= 1

    def test_delete_document(self, fts_tmp_db):
        fts_tmp_db.delete_document("c1")
        results = fts_tmp_db.search("Python")
        assert len(results) == 0

    def test_build_fts_query(self, fts_tmp_db):
        q = fts_tmp_db._build_fts_query("机器学习 Python")
        assert '"机器学习"' in q
        assert '"Python"' in q
        assert "AND" in q

    def test_empty_query(self, fts_tmp_db):
        q = fts_tmp_db._build_fts_query("")
        assert q == ""