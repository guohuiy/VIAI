"""
语义分块器
利用嵌入模型计算段落间相似度，动态分块
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.config import CHUNKING_CONFIG
from core.embedding import get_embedding


@dataclass
class Chunk:
    """文本分块"""
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    book_id: str = ""
    struct_path: str = ""
    content: str = ""
    token_count: int = 0
    embedding: Optional[List[float]] = None
    start_char: int = 0
    end_char: int = 0
    heading_stack: List[str] = field(default_factory=list)


class SemanticChunker:
    """语义分块器"""

    def __init__(self, target_tokens: int = None, min_tokens: int = None):
        self.target_tokens = target_tokens or CHUNKING_CONFIG["target_tokens"]
        self.min_tokens = min_tokens or CHUNKING_CONFIG["min_tokens"]

    def chunk_by_structure(
        self,
        raw_text: str,
        chapters: List[Dict[str, Any]],
        book_id: str = "",
        heading_stack: Optional[List[str]] = None,
    ) -> List[Chunk]:
        """
        按章节边界进行结构分块

        Args:
            raw_text: 原始文本
            chapters: 章节列表
            book_id: 书籍 ID
            heading_stack: 标题层级栈

        Returns:
            分块列表
        """
        if heading_stack is None:
            heading_stack = []

        lines = raw_text.split("\n")
        chunks = []

        if not chapters:
            # 无章节结构时，整体作为一个块
            chunk = Chunk(
                book_id=book_id,
                content=raw_text,
                token_count=len(raw_text),
                start_char=0,
                end_char=len(raw_text),
                heading_stack=list(heading_stack),
            )
            chunks.append(chunk)
            return chunks

        for ch in chapters:
            heading_stack.append(ch["title"])
            start_line = ch.get("start_line", 0)
            end_line = ch.get("end_line", len(lines))
            chapter_text = "\n".join(lines[start_line:end_line]).strip()

            # 计算字符位置
            start_char = sum(len(line) + 1 for line in lines[:start_line])
            end_char = start_char + len(chapter_text)

            if not chapter_text:
                heading_stack.pop()
                continue

            # 如果章节内容超过目标大小，递归分块
            if len(chapter_text) > self.target_tokens * 2:
                sub_chunks = self.chunk_by_structure(
                    chapter_text,
                    ch.get("children", []),
                    book_id,
                    heading_stack,
                )
                chunks.extend(sub_chunks)
            else:
                chunk = Chunk(
                    book_id=book_id,
                    struct_path=f"{book_id}/{ch['title']}",
                    content=chapter_text,
                    token_count=len(chapter_text),
                    start_char=start_char,
                    end_char=end_char,
                    heading_stack=list(heading_stack),
                )
                chunks.append(chunk)

            heading_stack.pop()

        return chunks

    def chunk_by_semantic(
        self,
        paragraphs: List[str],
        book_id: str = "",
        heading_stack: Optional[List[str]] = None,
    ) -> List[Chunk]:
        """
        基于语义相似度的动态分块

        Args:
            paragraphs: 段落列表
            book_id: 书籍 ID
            heading_stack: 标题层级栈

        Returns:
            分块列表
        """
        if heading_stack is None:
            heading_stack = []

        if len(paragraphs) <= 1:
            text = paragraphs[0] if paragraphs else ""
            return [Chunk(
                book_id=book_id,
                content=text,
                token_count=len(text),
                start_char=0,
                end_char=len(text),
                heading_stack=list(heading_stack),
            )]

        # 计算段落间相似度
        similarities = self._compute_paragraph_similarities(paragraphs)

        # 基于相似度变化点进行分块
        chunks = []
        current_paragraphs = [paragraphs[0]]
        char_offset = 0

        for i in range(1, len(paragraphs)):
            # 如果相似度骤降（语义变化），在此处分块
            if similarities[i - 1] < 0.5:
                chunk_text = "\n".join(current_paragraphs)
                end_char = char_offset + len(chunk_text)
                chunks.append(Chunk(
                    book_id=book_id,
                    content=chunk_text,
                    token_count=len(chunk_text),
                    start_char=char_offset,
                    end_char=end_char,
                    heading_stack=list(heading_stack),
                ))
                char_offset = end_char
                current_paragraphs = [paragraphs[i]]
            else:
                current_paragraphs.append(paragraphs[i])

        # 最后一块
        if current_paragraphs:
            chunk_text = "\n".join(current_paragraphs)
            chunks.append(Chunk(
                book_id=book_id,
                content=chunk_text,
                token_count=len(chunk_text),
                start_char=char_offset,
                end_char=len(chunk_text),
                heading_stack=list(heading_stack),
            ))

        return chunks

    def _compute_paragraph_similarities(self, paragraphs: List[str]) -> List[float]:
        """
        计算相邻段落间的语义相似度

        Args:
            paragraphs: 段落列表

        Returns:
            相邻段落相似度列表 (长度 = len(paragraphs) - 1)
        """

        if len(paragraphs) < 2:
            return []

        embeddings = []
        for para in paragraphs:
            emb = get_embedding(para[:512])  # 取前512字符
            embeddings.append(emb)

        similarities = []
        for i in range(len(embeddings) - 1):
            if embeddings[i] and embeddings[i + 1]:
                sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
                similarities.append(sim)
            else:
                similarities.append(0.0)

        return similarities

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        import math
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)
