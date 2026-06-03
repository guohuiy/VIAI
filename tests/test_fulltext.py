"""
测试全文检索引擎 - 使用独立的临时数据库
"""
import os
import sqlite3
import tempfile

import pytest

from retrieval.fulltext_engine import FullTextEngine


@pytest.fixture
def fts_tmp_db():
    """创建临时 FTS5 数据库"""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()

    # 初始化表和数据
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS books (id TEXT PRIMARY KEY, title TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS chunks (chunk_id TEXT PRIMARY KEY, book_id TEXT, content TEXT)")
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(chunk_id UNINDEXED, content)")
    conn.execute("INSERT INTO books VALUES ('b1', '测试书籍')")
    conn.execute("INSERT INTO chunks VALUES ('c1', 'b1', 'Python机器学习入门')")
    conn.execute("INSERT INTO chunks VALUES ('c2', 'b1', '深度学习与神经网络')")
    conn.execute("INSERT INTO fts_chunks VALUES ('c1', 'Python机器学习入门')")
    conn.execute("INSERT INTO fts_chunks VALUES ('c2', '深度学习与神经网络')")
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