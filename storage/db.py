"""
数据库连接与操作模块
封装 SQLite 的 CRUD 操作
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from core.config import STORAGE_CONFIG


class DatabaseManager:
    """SQLite 数据库管理器"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or STORAGE_CONFIG["sqlite"]
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    @property
    def conn(self) -> sqlite3.Connection:
        """获取数据库连接（懒加载）"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def _init_db(self) -> None:
        """初始化数据库表结构（支持旧表迁移）"""
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            self.conn.executescript(schema_sql)
            self.conn.commit()

        # 数据库迁移：为旧表补充新增字段
        self._migrate_add_column("books", "category", "TEXT DEFAULT ''")
        self._migrate_add_column("books", "file_hash", "TEXT DEFAULT ''")
        self._migrate_add_column("books", "language", "TEXT DEFAULT '中文'")
        self._migrate_add_column("books", "summary", "TEXT DEFAULT ''")

    def _migrate_add_column(self, table: str, column: str, col_def: str) -> None:
        """安全地给表增加一列（如果该列不存在）"""
        try:
            cursor = self.conn.execute(f"PRAGMA table_info({table})")
            existing_cols = {row["name"] for row in cursor.fetchall()}
            if column not in existing_cols:
                self.conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"
                )
                self.conn.commit()
                print(f"  [迁移] 表 {table} 增加字段: {column}")
        except Exception:
            pass  # 忽略迁移失败，不影响主流程

    # ========== 书籍操作 ==========

    def add_book(self, book_data: Dict[str, Any]) -> None:
        """添加书籍（支持新增加字段：category, file_hash, language, summary）"""
        self.conn.execute(
            """INSERT INTO books (id, title, author, file_path, category, file_hash, language, summary,
                                  total_chars, total_chunks, embedding_model)
               VALUES (:id, :title, :author, :file_path, :category, :file_hash, :language, :summary,
                       :total_chars, :total_chunks, :embedding_model)""",
            book_data,
        )
        self.conn.commit()

    def get_all_books(self) -> List[Dict[str, Any]]:
        """获取所有书籍"""
        cursor = self.conn.execute("SELECT * FROM books ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def get_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        """获取单本书籍"""
        cursor = self.conn.execute(
            "SELECT * FROM books WHERE id = ?", (book_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_book(self, book_id: str) -> None:
        """删除书籍及关联数据"""
        self.conn.execute("DELETE FROM chunks WHERE book_id = ?", (book_id,))
        self.conn.execute("DELETE FROM chapters WHERE book_id = ?", (book_id,))
        self.conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.conn.commit()

    # ========== 分块操作 ==========

    def add_chunk(self, chunk_data: Dict[str, Any]) -> None:
        """添加分块（单条）"""
        self.conn.execute(
            """INSERT INTO chunks (chunk_id, book_id, content, struct_path, start_char, end_char, heading_stack)
               VALUES (:chunk_id, :book_id, :content, :struct_path, :start_char, :end_char, :heading_stack)""",
            chunk_data,
        )
        self.conn.commit()

    def add_chunks_batch(self, chunk_records: List[Dict[str, Any]]) -> None:
        """批量添加分块（一次事务提交，大幅提升导入性能）"""
        cursor = self.conn.cursor()
        cursor.executemany(
            """INSERT INTO chunks (chunk_id, book_id, content, struct_path, start_char, end_char, heading_stack)
               VALUES (:chunk_id, :book_id, :content, :struct_path, :start_char, :end_char, :heading_stack)""",
            chunk_records,
        )
        self.conn.commit()

    def get_chunks_by_book(self, book_id: str) -> List[Dict[str, Any]]:
        """获取某本书的所有分块"""
        cursor = self.conn.execute(
            "SELECT * FROM chunks WHERE book_id = ? ORDER BY start_char",
            (book_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """获取单个分块"""
        cursor = self.conn.execute(
            "SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    # ========== 章节操作 ==========

    def add_chapter(self, chapter_data: Dict[str, Any]) -> None:
        """添加章节"""
        self.conn.execute(
            """INSERT INTO chapters (id, book_id, parent_id, level, title, start_char, end_char, summary, chunk_ids)
               VALUES (:id, :book_id, :parent_id, :level, :title, :start_char, :end_char, :summary, :chunk_ids)""",
            chapter_data,
        )
        self.conn.commit()

    def get_chapters_by_book(self, book_id: str) -> List[Dict[str, Any]]:
        """获取某本书的章节"""
        cursor = self.conn.execute(
            "SELECT * FROM chapters WHERE book_id = ? ORDER BY start_char",
            (book_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ========== 标签操作 ==========

    def add_chunk_tags(self, chunk_id: str, tags: List[str]) -> None:
        """为分块添加标签"""
        for tag in tags:
            self.conn.execute(
                "INSERT OR IGNORE INTO chunk_tags (chunk_id, tag) VALUES (?, ?)",
                (chunk_id, tag),
            )
        self.conn.commit()

    def get_chunks_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """按标签获取分块"""
        cursor = self.conn.execute(
            """SELECT c.* FROM chunks c
               JOIN chunk_tags t ON c.chunk_id = t.chunk_id
               WHERE t.tag = ?""",
            (tag,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None