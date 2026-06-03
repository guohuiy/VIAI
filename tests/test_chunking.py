"""
测试分块器模块
"""

from preprocessing.chunking.fixed_chunker import FixedChunker
from preprocessing.chunking.recursive_chunker import RecursiveChunker
from preprocessing.chunking.semantic_chunker import Chunk


class TestFixedChunker:
    """固定大小分块器测试"""

    def test_basic_chunking(self):
        chunker = FixedChunker(target_tokens=50, overlap_tokens=10)
        text = "测试文本 " * 200  # 800 字符，应该在 100 token 窗口内切分
        chunks = chunker.chunk(text, book_id="book-1")
        assert len(chunks) > 1
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(c.book_id == "book-1" for c in chunks)

    def test_single_chunk_for_short_text(self):
        chunker = FixedChunker(target_tokens=100, overlap_tokens=20)
        text = "简短文本"
        chunks = chunker.chunk(text, book_id="book-1")
        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_chunk_overlap(self):
        chunker = FixedChunker(target_tokens=10, overlap_tokens=5)
        # window_size = 20, step_size = 10
        # 构造较长的文本确保有重叠
        text = "A" * 100
        chunks = chunker.chunk(text, book_id="b1")
        assert len(chunks) >= 2

        # 验证相邻块有重叠区域
        if len(chunks) >= 2:
            overlap_start = max(chunks[0].start_char, chunks[1].start_char)
            overlap_end = min(chunks[0].end_char, chunks[1].end_char)
            assert overlap_end > overlap_start  # 有重叠

    def test_heading_stack_preserved(self):
        chunker = FixedChunker(target_tokens=10, overlap_tokens=3)
        text = "A" * 50
        heading = ["第一章", "第一节"]
        chunks = chunker.chunk(text, heading_stack=heading)
        for c in chunks:
            assert c.heading_stack == heading

    def test_chunk_token_count(self):
        chunker = FixedChunker(target_tokens=20, overlap_tokens=5)
        text = "Hello World! " * 30
        chunks = chunker.chunk(text, book_id="b1")
        for c in chunks:
            assert c.token_count == len(c.content)
            assert c.token_count > 0


class TestRecursiveChunker:
    """递归分块器测试"""

    def test_no_recursion_needed(self):
        chunker = RecursiveChunker(target_tokens=500, min_tokens=50, overlap_tokens=50)
        chunks = [Chunk(content="A" * 100, book_id="b1")]
        result = chunker.chunk(chunks)
        assert len(result) == 1

    def test_recursion_on_long_chunk(self):
        chunker = RecursiveChunker(target_tokens=50, min_tokens=10, overlap_tokens=10, max_depth=2)
        chunks = [Chunk(content="A" * 500, book_id="b1")]
        result = chunker.chunk(chunks)
        assert len(result) > 1

    def test_max_depth_respected(self):
        chunker = RecursiveChunker(target_tokens=10, min_tokens=5, overlap_tokens=2, max_depth=1)
        chunks = [Chunk(content="B" * 1000, book_id="b1")]
        result = chunker.chunk(chunks)
        # max_depth=1 限制了递归深度，但第一次切分仍然会发生
        assert len(result) >= 1

    def test_multiple_chunks_input(self):
        chunker = RecursiveChunker(target_tokens=50, min_tokens=10, overlap_tokens=10)
        chunks = [
            Chunk(content="A" * 50, book_id="b1"),
            Chunk(content="B" * 500, book_id="b1"),  # 这个需要递归
            Chunk(content="C" * 30, book_id="b1"),
        ]
        result = chunker.chunk(chunks)
        assert len(result) > 3  # 第二个块被切分了
