"""
上下文组装模块
将检索结果组装成 LLM 可用的上下文
"""

from typing import List, Dict, Any

from core.llm import estimate_tokens
from core.config import RETRIEVAL_CONFIG


class ContextAssembler:
    """上下文组装器"""

    def __init__(self, max_tokens: int = None):
        self.max_tokens = max_tokens or RETRIEVAL_CONFIG["max_context_tokens"]

    def assemble(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        max_tokens: int = None,
    ) -> str:
        """
        将检索结果组装成格式化的上下文字符串

        Args:
            retrieved_chunks: 检索结果列表
            max_tokens: 最大 token 限制

        Returns:
            组装后的上下文文本
        """
        max_t = max_tokens or self.max_tokens

        # 按原文顺序排列（保持逻辑连贯）
        sorted_chunks = sorted(
            retrieved_chunks,
            key=lambda c: (
                c.get("metadata", {}).get("book_id", ""),
                c.get("metadata", {}).get("start_char", 0),
            )
        )

        context_parts = []
        total_tokens = 0

        for chunk in sorted_chunks:
            metadata = chunk.get("metadata", {})
            book_title = metadata.get("book_title", "未知书籍")
            heading = metadata.get("heading", "")
            relevance = chunk.get("score", 0)

            # 构建格式化的素材块
            block = self._format_chunk(
                index=len(context_parts) + 1,
                book_title=book_title,
                heading=heading,
                relevance=relevance,
                content=chunk.get("content", ""),
            )

            tokens = estimate_tokens(block)
            if total_tokens + tokens > max_t:
                break

            context_parts.append(block)
            total_tokens += tokens

        return "\n".join(context_parts)

    def _format_chunk(
        self,
        index: int,
        book_title: str,
        heading: str,
        relevance: float,
        content: str,
    ) -> str:
        """格式化单个素材块"""
        return f"""## 素材 [{index}]
**来源**：《{book_title}》{heading}
**相关性**：{relevance:.2f}
**内容**：{content}
"""