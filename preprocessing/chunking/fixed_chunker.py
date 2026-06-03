"""
固定大小分块器
对超长连续文本使用滑动窗口分块
"""

from typing import List, Optional

from core.config import CHUNKING_CONFIG

from .semantic_chunker import Chunk


class FixedChunker:
    """固定大小分块器（滑动窗口）"""

    def __init__(
        self,
        target_tokens: int = None,
        overlap_tokens: int = None,
    ):
        self.target_tokens = target_tokens or CHUNKING_CONFIG["target_tokens"]
        self.overlap_tokens = overlap_tokens or CHUNKING_CONFIG["overlap_tokens"]

    def chunk(
        self,
        text: str,
        book_id: str = "",
        heading_stack: Optional[List[str]] = None,
    ) -> List[Chunk]:
        """
        固定大小滑动窗口分块

        Args:
            text: 输入文本
            book_id: 书籍 ID
            heading_stack: 标题层级栈

        Returns:
            分块列表
        """
        if heading_stack is None:
            heading_stack = []

        chunks = []
        char_offset = 0
        text_length = len(text)

        # 粗略估算：中英文混合场景，1 token ≈ 2 字符
        window_size = self.target_tokens * 2
        step_size = window_size - self.overlap_tokens * 2

        while char_offset < text_length:
            end = min(char_offset + window_size, text_length)
            chunk_text = text[char_offset:end]

            chunk = Chunk(
                book_id=book_id,
                content=chunk_text,
                token_count=len(chunk_text),
                start_char=char_offset,
                end_char=end,
                heading_stack=list(heading_stack),
            )
            chunks.append(chunk)

            char_offset += step_size
            if char_offset >= text_length:
                break

        return chunks
