"""
递归分块器
当分块后仍有超长块时，递归切分至目标大小（带最大深度限制）
"""

from typing import List, Optional
from .semantic_chunker import Chunk
from .fixed_chunker import FixedChunker
from core.config import CHUNKING_CONFIG


class RecursiveChunker:
    """递归分块器（带深度限制和最小块保护）"""

    def __init__(
        self,
        target_tokens: int = None,
        min_tokens: int = None,
        overlap_tokens: int = None,
        max_depth: int = 3,
    ):
        self.target_tokens = target_tokens or CHUNKING_CONFIG["target_tokens"]
        self.min_tokens = min_tokens or CHUNKING_CONFIG["min_tokens"]
        self.overlap_tokens = overlap_tokens or CHUNKING_CONFIG["overlap_tokens"]
        self.max_depth = max_depth
        self._fixed_chunker = FixedChunker(
            target_tokens=self.target_tokens,
            overlap_tokens=self.overlap_tokens,
        )

    def chunk(
        self,
        chunks: List[Chunk],
        book_id: str = "",
        depth: int = 0,
    ) -> List[Chunk]:
        """
        递归切分超长块（带深度限制）

        Args:
            chunks: 输入的分块列表
            book_id: 书籍 ID
            depth: 当前递归深度

        Returns:
            递归切分后的分块列表
        """
        if depth > self.max_depth:
            return chunks

        # 字符级别的阈值：1 token ≈ 2 字符
        char_threshold = self.target_tokens * 3  # 512 * 3 = 1536 字符
        min_char = self.min_tokens * 1  # 128 字符以下不再切分

        result = []
        for chunk in chunks:
            char_count = len(chunk.content)

            if char_count > char_threshold and char_count > min_char:
                # 超长块，需要切分
                sub_chunks = self._fixed_chunker.chunk(
                    text=chunk.content,
                    book_id=book_id or chunk.book_id,
                    heading_stack=chunk.heading_stack,
                )

                # 递归处理子块（depth+1）
                result.extend(self.chunk(sub_chunks, book_id, depth + 1))
            else:
                result.append(chunk)

        return result