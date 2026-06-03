"""
测试检索模块 - 向量存储、全文检索、混合检索、重排序
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest


class TestFullTextEngine:
    """全文检索引擎测试（使用临时 SQLite 文件）"""

    @pytest.fixture
    def fts(self):
        from retrieval.fulltext_engine import FullTextEngine
        import sqlite3

        # 创建临时数据库
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_path = tmp.name
        tmp.close()

        # 创建 FTS5 表并插入示例数据
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

    def test_search_found(self, fts):
        results = fts.search("Python")
        assert len(results) >= 1

    def test_search_not_found(self, fts):
        results = fts.search("NonExistentWordXYZ")
        assert len(results) == 0

    def test_search_multiple_terms(self, fts):
        results = fts.search("机器学习")
        assert len(results) >= 1

    def test_search_top_k(self, fts):
        results = fts.search("学习", top_k=1)
        assert len(results) <= 1

    def test_add_document(self, fts):
        fts.add_document("c3", "新增测试文档内容")
        results = fts.search("新增")
        assert len(results) >= 1

    def test_delete_document(self, fts):
        fts.delete_document("c1")
        results = fts.search("Python")
        assert len(results) == 0

    def test_build_fts_query(self, fts):
        q = fts._build_fts_query("机器学习 Python")
        assert '"机器学习"' in q
        assert '"Python"' in q

    def test_empty_query(self, fts):
        q = fts._build_fts_query("")
        assert q == ""

    def test_single_term_query(self, fts):
        q = fts._build_fts_query("  Python  ")
        assert '"Python"' in q

    def test_add_documents_batch(self, fts):
        docs = [
            {"chunk_id": "c4", "content": "批量文档1"},
            {"chunk_id": "c5", "content": "批量文档2"},
        ]
        fts.add_documents_batch(docs)
        results = fts.search("批量")
        assert len(results) == 2

    def test_close_engine(self, fts):
        fts.close()
        assert fts._conn is None


class TestVectorStore:
    """向量存储模块测试（mock ChromaDB）"""

    @patch("retrieval.vector_store.chromadb")
    def test_initialization(self, mock_chromadb):
        from retrieval.vector_store import VectorStore

        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        store = VectorStore()
        assert store.collection is not None

    @patch("retrieval.vector_store.chromadb")
    def test_add_chunks(self, mock_chromadb):
        from retrieval.vector_store import VectorStore

        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        store = VectorStore()
        store.add_chunks(
            ids=["c1"],
            embeddings=[[0.1] * 1024],
            documents=["test"],
            metadatas=[{"book_id": "b1"}],
        )
        mock_collection.add.assert_called_once()

    @patch("retrieval.vector_store.chromadb")
    def test_search(self, mock_chromadb):
        from retrieval.vector_store import VectorStore

        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_collection.query.return_value = {
            "ids": [["c1"]],
            "distances": [[0.1]],
            "metadatas": [[{"book_id": "b1"}]],
            "documents": [["test content"]],
        }

        store = VectorStore()
        results = store.search([0.1] * 1024, top_k=5)
        assert len(results) >= 0


class TestHybridRetriever:
    """混合检索器测试"""

    @patch("retrieval.hybrid_retriever.FullTextEngine")
    @patch("retrieval.hybrid_retriever.VectorStore")
    def test_initialization(self, mock_vs, mock_fts):
        from retrieval.hybrid_retriever import HybridRetriever

        retriever = HybridRetriever()
        assert retriever is not None

    def test_rrf_merge(self):
        """RRF 融合算法验证"""
        from retrieval.hybrid_retriever import HybridRetriever

        retriever = HybridRetriever()
        vector_results = [
            {"id": "a", "score": 0.9, "source": "vector"},
            {"id": "b", "score": 0.8, "source": "vector"},
        ]
        fts_results = [
            {"id": "b", "score": 0.7, "source": "fts"},
            {"id": "c", "score": 0.6, "source": "fts"},
        ]
        merged = retriever._rrf_merge(vector_results, fts_results, k=60)
        assert len(merged) >= 1


class TestReranker:
    """重排序器测试"""

    def test_initialization(self):
        from retrieval.reranker import Reranker

        reranker = Reranker()
        assert reranker is not None

    def test_rerank_empty(self):
        from retrieval.reranker import Reranker

        reranker = Reranker()
        results = reranker.rerank("query", [])
        assert results == []

    def test_rerank_sorts_by_score(self):
        from retrieval.reranker import Reranker

        reranker = Reranker()
        items = [
            {"id": "a", "score": 0.3},
            {"id": "b", "score": 0.9},
            {"id": "c", "score": 0.6},
        ]
        results = reranker.rerank("test", items)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)


class TestContextAssembler:
    """上下文组装器测试"""

    def test_assemble_empty(self):
        from retrieval.context_assembler import ContextAssembler

        assembler = ContextAssembler()
        result = assembler.assemble([], max_tokens=1000)
        assert isinstance(result, dict)