"""
SQLite FTS5 全文检索引擎
提供关键词搜索功能
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

from core.config import STORAGE_CONFIG


class FullTextEngine:
    """SQLite FTS5 全文检索引擎"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or STORAGE_CONFIG["sqlite"]
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        """获取数据库连接（懒加载）"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            # 与 DatabaseManager 使用相同的 WAL 模式，避免锁冲突
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def search(
        self,
        query: str,
        top_k: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        全文检索

        Args:
            query: 关键词查询
            top_k: 返回顶部 K 个结果

        Returns:
            检索结果列表
        """
        # FTS5 查询语法
        fts_query = self._build_fts_query(query)

        cursor = self.conn.execute(
            """
            SELECT c.chunk_id, c.content, c.book_id, c.struct_path,
                   c.start_char, c.end_char, c.heading_stack,
                   b.title as book_title
            FROM fts_chunks f
            JOIN chunks c ON f.chunk_id = c.chunk_id
            JOIN books b ON c.book_id = b.id
            WHERE fts_chunks MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_query, top_k),
        )

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["chunk_id"],
                "content": row["content"],
                "metadata": {
                    "book_id": row["book_id"],
                    "book_title": row["book_title"],
                    "struct_path": row["struct_path"],
                    "start_char": row["start_char"],
                    "end_char": row["end_char"],
                    "heading_stack": row["heading_stack"],
                },
                "score": 1.0,
                "source": "fts",
            })

        return results

    def add_document(
        self,
        chunk_id: str,
        content: str,
    ) -> None:
        """添加文档到全文索引"""
        self.conn.execute(
            "INSERT INTO fts_chunks (chunk_id, content) VALUES (?, ?)",
            (chunk_id, content),
        )
        self.conn.commit()

    def add_documents_batch(
        self,
        documents: List[Dict[str, str]],
    ) -> None:
        """批量添加文档"""
        cursor = self.conn.cursor()
        cursor.executemany(
            "INSERT INTO fts_chunks (chunk_id, content) VALUES (:chunk_id, :content)",
            documents,
        )
        self.conn.commit()

    def delete_document(self, chunk_id: str) -> None:
        """删除文档索引"""
        self.conn.execute(
            "DELETE FROM fts_chunks WHERE chunk_id = ?",
            (chunk_id,),
        )
        self.conn.commit()

    def _build_fts_query(self, query: str) -> str:
        """
        构建 FTS5 查询字符串

        Args:
            query: 原始查询关键词

        Returns:
            FTS5 格式查询字符串
        """
        # 按空格分词，每个词作为 AND 条件
        terms = query.strip().split()
        if not terms:
            return ""

        # 使用 NEAR 或 AND 连接
        fts_parts = []
        for term in terms:
            # 对中文词进行转义
            fts_parts.append(f'"{term}"')

        return " AND ".join(fts_parts)

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None