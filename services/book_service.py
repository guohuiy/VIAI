"""
书籍入库服务
处理电子书从解析、分块到入库的完整流程

2026-06-01 重构：
  - 支持分类标签（category）
  - MD5 文件去重
  - 语言类型自动检测
  - 批量写入 chunks
  - 自动摘要生成
"""

import uuid
import json
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path

from preprocessing.parsers.txt_parser import TxtParser
from preprocessing.parsers.pdf_parser import PdfParser
from preprocessing.structure.chapter_detector import detect_structure
from preprocessing.chunking.semantic_chunker import SemanticChunker
from preprocessing.chunking.recursive_chunker import RecursiveChunker
from retrieval.vector_store import VectorStore
from retrieval.fulltext_engine import FullTextEngine
from storage.db import DatabaseManager
from core.config import STORAGE_CONFIG


def detect_language(content: str) -> str:
    """检测文本语言类型"""
    if not content:
        return "未知"
    total = len(content)
    if total == 0:
        return "未知"
    chinese = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
    english = sum(1 for c in content if c.isascii() and c.isalpha())
    ratio_cn = chinese / total
    ratio_en = english / total
    if ratio_cn > 0.8:
        return "中文"
    elif ratio_cn > 0.3:
        return "中英混合"
    elif ratio_en > 0.3:
        return "英文"
    else:
        return "其他"


def compute_file_hash(file_path: str) -> str:
    """计算文件 MD5 哈希"""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_summary(content: str, max_len: int = 200) -> str:
    """从内容头部提取摘要（前1-2个完整句子）"""
    for sep in ['。', '！', '？', '\n']:
        parts = content[:500].split(sep)
        if len(parts) >= 2:
            summary = parts[0] + sep + parts[1][:100]
            return summary.strip()[:max_len]
    if content:
        return content[:max_len].strip()
    return ""


def infer_category_from_path(file_path: str, books_root_dirs: Optional[List[str]] = None) -> str:
    """
    从文件路径推断分类名
    例如 C:/books/历史军事/xxx.txt → "历史军事"
    """
    path = Path(file_path)
    # 从相对路径中找：看父目录
    parent = path.parent
    if parent.name and parent.name not in ("raw_books", "books", "data"):
        return parent.name
    # 找祖父目录
    grandparent = parent.parent if parent.parent else None
    if grandparent and grandparent.name not in ("raw_books", "books", "data"):
        return grandparent.name
    return "未分类"


class BookService:
    """书籍入库服务"""

    def __init__(self):
        self.txt_parser = TxtParser()
        self.pdf_parser = PdfParser()
        self.semantic_chunker = SemanticChunker()
        self.recursive_chunker = RecursiveChunker()
        self.vector_store = VectorStore()
        self.fulltext = FullTextEngine()
        self.db = DatabaseManager()

    def import_book(
        self,
        file_path: str,
        category: str = "",
        compute_vector: bool = False,
    ) -> Dict[str, Any]:
        """
        导入一本电子书（完整流程）

        Args:
            file_path: 电子书文件路径
            category: 分类标签（如：历史军事、幽默笑话）
            compute_vector: 是否立即计算向量（默认False用零向量占位）

        Returns:
            处理报告
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return {"status": "error", "error": f"文件不存在: {file_path}"}

        # 1. 文件基本元数据
        file_md5 = compute_file_hash(str(file_path))
        file_size = file_path.stat().st_size

        # 2. 文档解析
        if self.txt_parser.supports(str(file_path)):
            parse_result = self.txt_parser.parse(str(file_path))
        elif self.pdf_parser.supports(str(file_path)):
            parse_result = self.pdf_parser.parse(str(file_path))
        else:
            return {"status": "error", "error": f"不支持的文件格式: {file_path.suffix}"}

        raw_text = "\n".join(page.text for page in parse_result.pages)

        # 3. 章节识别（批量导入时关闭 LLM 推理，仅用正则加速）
        structure = detect_structure(raw_text, use_llm=False)
        title = structure.get("title", file_path.stem)
        book_id = str(uuid.uuid4())

        # 4. 语言检测
        language = detect_language(raw_text)

        # 5. 摘要
        summary = extract_summary(raw_text)

        # 6. 语义分块
        chunks = self.semantic_chunker.chunk_by_structure(
            raw_text, structure.get("chapters", []), book_id
        )

        # 对超长块进行递归分块
        chunks = self.recursive_chunker.chunk(chunks, book_id)

        # 7. 入库
        self._index_chunks(chunks, book_id, title, str(file_path), compute_vector)

        # 8. 保存书籍元数据
        self.db.add_book({
            "id": book_id,
            "title": title,
            "author": "",
            "file_path": str(file_path),
            "category": category or infer_category_from_path(str(file_path)),
            "file_hash": file_md5,
            "language": language,
            "summary": summary,
            "total_chars": parse_result.total_chars,
            "total_chunks": len(chunks),
            "embedding_model": "bge-m3",
        })

        return {
            "status": "success",
            "book_id": book_id,
            "title": title,
            "total_chars": parse_result.total_chars,
            "total_chunks": len(chunks),
            "chapters": len(structure.get("chapters", [])),
            "category": category,
            "language": language,
            "file_md5": file_md5,
            "file_size_kb": round(file_size / 1024, 1),
        }

    def _index_chunks(
        self,
        chunks: List[Any],
        book_id: str,
        book_title: str,
        file_path: str,
        compute_vector: bool = False,
    ) -> None:
        """
        对分块进行入库

        Args:
            chunks: 分块列表
            book_id: 书籍 ID
            book_title: 书籍标题
            file_path: 文件路径
            compute_vector: 是否立即计算向量（True=实时计算，False=零向量占位）
        """
        chunk_ids = []
        embeddings = []
        documents = []
        metadatas = []
        fts_docs = []
        chunk_records = []

        for chunk in chunks:
            chunk_id = chunk.chunk_id
            content = chunk.content

            if not content.strip():
                continue

            chunk_ids.append(chunk_id)
            embeddings.append([0.0] * 1024)  # 零向量占位
            documents.append(content)
            metadatas.append({
                "book_id": book_id,
                "book_title": book_title,
                "struct_path": chunk.struct_path,
                "token_count": chunk.token_count,
                "heading": chunk.heading_stack[-1] if chunk.heading_stack else "",
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
            })
            fts_docs.append({
                "chunk_id": chunk_id,
                "content": content,
            })
            chunk_records.append({
                "chunk_id": chunk_id,
                "book_id": book_id,
                "content": content,
                "struct_path": chunk.struct_path,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "heading_stack": json.dumps(chunk.heading_stack, ensure_ascii=False),
            })

        # 写入 ChromaDB（零向量占位，后续可重建）
        if chunk_ids:
            self.vector_store.add_chunks(chunk_ids, embeddings, documents, metadatas)

        # 写入全文索引
        if fts_docs:
            self.fulltext.add_documents_batch(fts_docs)

        # 批量写入分块记录（一次事务提交）
        if chunk_records:
            self.db.add_chunks_batch(chunk_records)

    def list_books(self) -> List[Dict[str, Any]]:
        """列出所有已入库的书籍"""
        return self.db.get_all_books()

    def delete_book(self, book_id: str) -> bool:
        """删除书籍及其所有索引"""
        chunks = self.db.get_chunks_by_book(book_id)
        chunk_ids = [c["chunk_id"] for c in chunks]

        if chunk_ids:
            self.vector_store.delete_chunks(chunk_ids)

        for cid in chunk_ids:
            self.fulltext.delete_document(cid)

        self.db.delete_book(book_id)
        return True

    def get_book_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """通过文件 MD5 查找是否已导入"""
        books = self.db.get_all_books()
        for b in books:
            if b.get("file_hash") == file_hash:
                return b
        return None