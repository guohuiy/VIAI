"""
重建向量索引脚本
为所有以零向量占位的 chunk 重新生成真实的 embedding 向量

重要：
  - FTS5 全文索引在导入时已经构建，此脚本不再重复重建
  - 向量生成使用 llama-embedding.exe，每个 chunk 单独调用
  - 对于大批量数据（如 3万+本书），建议分批执行

用法：
  python scripts/build_index.py                       # 全部重建
  python scripts/build_index.py --batch-size 50       # 每批50个chunk
  python scripts/build_index.py --book-id <id>        # 只重建单本书
  python scripts/build_index.py --skip-existing       # 跳过已有关闭向量
"""

import io
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.embedding import get_batch_embeddings  # noqa: E402
from retrieval.vector_store import VectorStore  # noqa: E402
from storage.db import DatabaseManager  # noqa: E402


def main():
    import argparse
    parser = argparse.ArgumentParser(description="重建向量索引")
    parser.add_argument("--batch-size", type=int, default=20,
                        help="每批处理的 chunk 数量（默认20），GPU小建议设小")
    parser.add_argument("--book-id", type=str, default=None,
                        help="只重建指定书籍的索引")
    parser.add_argument("--skip-existing", action="store_true",
                        help="跳过已有非零向量的 chunk")
    parser.add_argument("--limit", type=int, default=0,
                        help="最多处理多少 chunk（0=不限制，用于测试）")
    args = parser.parse_args()

    print("🔨 开始重建向量索引...")
    print(f"   模式: {'单本书' if args.book_id else '全量'}")
    print(f"   批次大小: {args.batch_size}")
    print(f"   跳过已有向量: {'是' if args.skip_existing else '否'}")
    print()

    db = DatabaseManager()
    vector_store = VectorStore()

    # 获取所有书籍或单本书
    if args.book_id:
        book = db.get_book(args.book_id)
        books = [book] if book else []
        if not books:
            print(f"❌ 未找到书籍: {args.book_id}")
            return
    else:
        books = db.get_all_books()
        if not books:
            print("📚 暂无已导入的书籍")
            return

    print(f"📖 共 {len(books)} 本书需处理\n")

    total_chunks = 0
    processed = 0
    failed = 0
    skipped = 0
    start_time = time.time()
    for book_idx, book in enumerate(books):
        book_id = book["id"]
        title = book["title"]
        chunks = db.get_chunks_by_book(book_id)
        if not chunks:
            continue

        total_chunks += len(chunks)

        # 分批处理 chunks（先收集一批，批量生成向量，批量写入）
        for batch_start in range(0, len(chunks), args.batch_size):
            batch = chunks[batch_start:batch_start + args.batch_size]

            # ---- 过滤：跳过已有非零向量 ----
            batch_ids = []
            batch_docs = []
            batch_metadata = []
            batch_to_process = []

            for chunk in batch:
                chunk_id = chunk["chunk_id"]
                if args.skip_existing:
                    try:
                        result = vector_store.collection.get(
                            ids=[chunk_id],
                            include=["embeddings"]
                        )
                        existing = result.get("embeddings")
                        if existing and existing[0] and any(v != 0 for v in existing[0][:10]):
                            skipped += 1
                            continue
                    except Exception:
                        pass
                batch_to_process.append(chunk)

            if not batch_to_process:
                continue

            # ---- 批量生成向量 ----
            try:
                texts = [ch["content"][:512] for ch in batch_to_process]
                embeddings = get_batch_embeddings(texts, batch_size=args.batch_size)
            except Exception as e:
                for ch in batch_to_process:
                    failed += 1
                    if failed <= 5:
                        print(f"    ⚠️  批量向量化失败: {str(e)[:80]}")
                continue

            # ---- 收集数据 ----
            for i, chunk in enumerate(batch_to_process):
                if i < len(embeddings):
                    batch_ids.append(chunk["chunk_id"])
                    batch_docs.append(chunk["content"])
                    batch_metadata.append({
                        "book_id": book_id,
                        "book_title": title,
                        "struct_path": chunk["struct_path"],
                        "heading": "",
                    })

            # ---- 批量写入 ChromaDB ----
            if batch_ids:
                try:
                    vector_store.add_chunks(
                        ids=batch_ids,
                        embeddings=embeddings[:len(batch_ids)],
                        documents=batch_docs,
                        metadatas=batch_metadata,
                    )
                    processed += len(batch_ids)
                except Exception as e:
                    for _ in batch_ids:
                        failed += 1
                        if failed <= 5:
                            print(f"    ⚠️  批量写入失败: {str(e)[:80]}")

        # 进度显示（每10本或最后几本）
        now = time.time()
        batch_done = processed + failed + skipped
        show_progress = (
            book_idx == 0 or
            (book_idx + 1) % 10 == 0 or
            book_idx >= len(books) - 3 or
            batch_done >= args.limit
        )
        if show_progress:
            elapsed = now - start_time
            speed = processed / max(elapsed, 1)
            eta = (total_chunks - batch_done) / max(speed, 0.1)
            ch = len(chunks)
            print(f"  [{book_idx+1}/{len(books)}] {title[:25]:<25s} "
                  f"{ch:>4d}个chunk | 已处理 {batch_done}/{total_chunks}向量 | "
                  f"{speed:.1f}向量/秒 | ETA: {eta:.0f}s")

        if args.limit > 0 and batch_done >= args.limit:
            print(f"\n  ⏹️  达到 --limit {args.limit} 限制，停止处理")
            break

    # 总结
    elapsed = time.time() - start_time
    print(f"\n{'='*50}")
    print("📊 索引重建完成")
    print(f"{'='*50}")
    print(f"  总 books:  {len(books)}")
    print(f"  总 chunks: {total_chunks}")
    print(f"  已处理:    {processed} ✅")
    print(f"  失败:      {failed} ⚠️")
    print(f"  跳过:      {skipped} ⏭️")
    print(f"  总耗时:    {elapsed:.0f}秒 ({elapsed/60:.1f}分钟)")


if __name__ == "__main__":
    main()
