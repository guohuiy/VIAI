"""
知识库构建流程 Demo 版
验证：编码修复 + 章节检测 + 多策略分块 + 分类增强 + 元数据存储

用法：
  python scripts/demo_knowledge_base.py --dir "C:/Users/huiya/Desktop/books/幽默笑话"
  python scripts/demo_knowledge_base.py --dir "C:/Users/huiya/Desktop/books" --count 20
  python scripts/demo_knowledge_base.py --full
"""

import json
import os
import random
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# 确保项目根目录在路径中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ════════════════════════════════════════════════════════════
# 配置
# ════════════════════════════════════════════════════════════

DEMO_DB_PATH = Path(__file__).parent.parent / "data" / "demo_library.db"
DEMO_OUTPUT = Path(__file__).parent.parent / "runtime" / "demo_build_report.json"

# ════════════════════════════════════════════════════════════
# 修复1：增强版编码检测
# ════════════════════════════════════════════════════════════

# 常见中文编码列表（按优先级排列）
CHINESE_ENCODINGS = ["gb18030", "gbk", "gb2312", "utf-8", "big5", "utf-16"]

def robust_detect_encoding(file_path: str) -> str:
    """
    增强版编码检测
    1. 先用 chardet 检测
    2. chardet 结果不可靠时，逐个尝试常见中文编码
    3. 用实际读取成功与否做最终判定
    """
    CHINESE_ENCODINGS_LIST = ["gb18030", "gbk", "gb2312", "utf-8", "big5", "utf-16"]

    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        raw_data = f.read(min(1024 * 100, file_size))

    # 检查是否包含中文字符（检查高位字节 0x81-0xFE）
    has_high_bytes = any(0x81 <= raw_data[i] <= 0xFE for i in range(min(len(raw_data), 1000)))

    # 尝试用 chardet 检测（捕获可能的版本兼容性异常）
    try:
        import chardet
        detect_result = chardet.detect(raw_data)
        detected_enc = detect_result.get("encoding", "").lower() if detect_result.get("encoding") else ""
        confidence = detect_result.get("confidence", 0)
    except Exception:
        detected_enc = ""
        confidence = 0

    # 如果 chardet 给出了可靠的中文编码结果，直接使用
    reliable_chinese = {"gb2312", "gbk", "gb18030", "big5", "utf-8", "utf-16", "utf-16le", "utf-16be"}
    if confidence > 0.5 and detected_enc in reliable_chinese:
        if detected_enc in ("gb2312", "gbk"):
            return "gb18030"
        if detected_enc.startswith("utf-16"):
            return "utf-16"
        return detected_enc

    # chardet 结果不可靠（如 koi8-u/iso8859/ascii 等非中文编码），但有高位字节 → 强制尝试中文编码
    if has_high_bytes:
        for enc in CHINESE_ENCODINGS_LIST:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    f.read(200)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue

    # 无高位字节或所有中文编码都失败 → 用 chardet 结果或 utf-8
    if detected_enc and confidence > 0.1:
        return detected_enc

    return "utf-8"

def read_with_encoding(file_path: str) -> tuple[str, str]:
    """读取文件内容，返回 (内容文本, 实际编码)"""
    encoding = robust_detect_encoding(file_path)
    try:
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            content = f.read()
        return content, encoding
    except Exception:
        # 终极兜底
        with open(file_path, "rb") as f:
            content = f.read().decode("utf-8", errors="replace")
        return content, "utf-8(force)"

# ════════════════════════════════════════════════════════════
# 修复2：增强版章节检测
# ════════════════════════════════════════════════════════════

def detect_chapters_regex(text: str) -> List[Dict[str, Any]]:
    """
    多重正则章节检测

    支持的模式（按优先级）：
    1. 第X章 / 第X回 / 第X节 / 第X部分
    2. Book X / Chapter X / Section X (英文)
    3. 一、/ 二、/ 三、...（中文数字序号）
    4. 1.1 / 1.2 / 2.1（数字编号）
    5. 一、/ 二、/ 三、... 单独成行
    6. 括号序号：（一）（二）（三）
    7. Part X / Volume X
    """
    import re

    chapters = []
    lines = text.split('\n')

    patterns = [
        # 1. 第X章/第X回/第X节/第X部分/第X卷
        (r'^\s*(第[一二三四五六七八九十百千万\d]+[章节回部卷篇集])(.*)$', 1),
        # 2. Book/Chapter/Section/Part X
        (r'^\s*(Book|Chapter|Section|Part|Volume)\s+([\dIVXLC]+)[\.\s:]*(.*)$', 1, 2),
        # 3. 中文数字序号：一、/ 二、/ 三、
        (r'^\s*([一二三四五六七八九十百千万]+)[、\.\s]+(.+)$', 1),
        # 4. 数字编号：1. / 1.1 / 1.1.1
        (r'^\s*(\d+(?:\.\d+)*)[\s\.]+(.+)$', 1),
        # 5. 括号序号：（一）（二）
        (r'^\s*[（\(]([一二三四五六七八九十]+)[）\)]\s*(.*)$', 1),
        # 6. Part One / Chapter One
        (r'^\s*(Part|Chapter|Section)\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)[\.\s:]*(.*)$', 1, 2),
    ]

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        for pattern_group in patterns:
            pattern = pattern_group[0]
            match = re.match(pattern, stripped)
            if match:
                if len(pattern_group) > 1 and pattern_group[1] == 2:
                    # English patterns
                    level = 1 if pattern_group[0].startswith(r'^\s*(Book|Part|Volume)') else 2
                    chapters.append({
                        "level": level,
                        "title": stripped,
                        "start_line": i,
                        "end_line": i + 1,
                    })
                else:
                    # Chinese patterns - determine level
                    num_part = match.group(1)
                    if '章' in num_part or '回' in num_part:
                        level = 1
                    elif '节' in num_part:
                        level = 2
                    elif '卷' in num_part or '部' in num_part or '篇' in num_part or '集' in num_part:
                        level = 1
                    else:
                        level = 2
                    chapters.append({
                        "level": level,
                        "title": stripped,
                        "start_line": i,
                        "end_line": i + 1,
                    })
                break  # 用第一个匹配到的模式

    # 后处理：合并相邻行，修正层级
    if not chapters:
        return []

    # 设置 end_line 为下一个章节的开始
    for i in range(len(chapters) - 1):
        chapters[i]["end_line"] = chapters[i + 1]["start_line"]

    return chapters

# ════════════════════════════════════════════════════════════
# 分块
# ════════════════════════════════════════════════════════════

@dataclass
class Chunk:
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    book_id: str = ""
    category: str = ""
    content: str = ""
    struct_path: str = ""
    start_char: int = 0
    end_char: int = 0
    heading: str = ""
    token_count: int = 0
    embedding: Optional[List[float]] = None

def chunk_by_chapters(text: str, chapters: List[Dict], book_id: str, category: str = "") -> List[Chunk]:
    """按章节边界分块"""
    if not chapters:
        # 无章节结构，整体作为一个块
        return [Chunk(
            book_id=book_id,
            category=category,
            content=text[:5000],
            start_char=0,
            end_char=min(len(text), 5000),
            token_count=len(text[:5000]),
        )]

    lines = text.split('\n')
    chunks = []

    for ch in chapters:
        start = ch["start_line"]
        end = min(ch["end_line"], len(lines))
        chapter_text = '\n'.join(lines[start:end]).strip()

        if not chapter_text:
            continue

        # 计算字符位置
        start_char = sum(len(line) + 1 for line in lines[:start])
        end_char = start_char + len(chapter_text)

        # 如果章节太长，进一步切分
        if len(chapter_text) > 3000:
            # 按段落分
            paragraphs = [p for p in chapter_text.split('\n') if p.strip()]
            sub_text = ""
            sub_start = start_char
            for para in paragraphs:
                if len(sub_text) + len(para) > 2000 and sub_text:
                    # 切分
                    chunks.append(Chunk(
                        book_id=book_id,
                        category=category,
                        content=sub_text.strip(),
                        struct_path=f"{book_id}/{ch['title']}",
                        start_char=sub_start,
                        end_char=sub_start + len(sub_text),
                        heading=ch['title'],
                        token_count=len(sub_text),
                    ))
                    sub_text = para
                    sub_start = sub_start + len(sub_text) - len(para)
                else:
                    sub_text += para + '\n'

            # 最后一段
            if sub_text.strip():
                chunks.append(Chunk(
                    book_id=book_id,
                    category=category,
                    content=sub_text.strip(),
                    struct_path=f"{book_id}/{ch['title']}",
                    start_char=sub_start,
                    end_char=sub_start + len(sub_text),
                    heading=ch['title'],
                    token_count=len(sub_text),
                ))
        else:
            chunks.append(Chunk(
                book_id=book_id,
                category=category,
                content=chapter_text,
                struct_path=f"{book_id}/{ch['title']}",
                start_char=start_char,
                end_char=end_char,
                heading=ch['title'],
                token_count=len(chapter_text),
            ))

    return chunks

# ════════════════════════════════════════════════════════════
# 摘要生成（使用 LLM）
# ════════════════════════════════════════════════════════════

def generate_book_summary(content: str, title: str) -> str:
    """
    使用 Qwen3.5 生成书籍摘要
    如果 LLM 不可用，返回基于头部的简单摘要
    """
    try:
        # 尝试调用 LLM
        from core.llm import call_llm
        prompt = f"""请为以下书籍生成一段简短的摘要（100字以内），概括其核心内容和主题。

书名：{title}

书籍开头内容：
{content[:1500]}

摘要："""
        response = call_llm(prompt, max_tokens=200)
        return response.strip()
    except Exception:
        # LLM 不可用时，从头部提取前两个句子
        sentences = []
        for sep in ['。', '！', '？', '\n']:
            parts = content[:500].split(sep)
            if len(parts) >= 2:
                sentences = parts[:2]
                break
        if sentences:
            return sentences[0] + sentences[1][:100] if len(sentences) > 1 else sentences[0][:200]
        return content[:200]

# ════════════════════════════════════════════════════════════
# Demo 主流程
# ════════════════════════════════════════════════════════════

def demo_build_knowledge_base(books_dir: str, max_books: int = 0, category_filter: str = None):
    """
    知识库构建 Demo 主流程

    Args:
        books_dir: 书籍根目录
        max_books: 最大处理数量（0=全部）
        category_filter: 分类过滤（如"幽默笑话"）
    """
    start_time = time.time()

    books_root = Path(books_dir)
    if not books_root.exists():
        print(f"❌ 目录不存在: {books_dir}")
        return

    # 收集所有书籍
    print("=" * 60)
    print("📚 知识库构建 Demo v1.0")
    print("=" * 60)

    all_books = []
    categories = []

    # Step 0: 扫描目录结构
    print("\n📂 正在扫描目录结构...")

    # 判断 books_dir 是根目录(含分类子目录)还是单个分类目录
    subdirs = [d for d in books_root.iterdir() if d.is_dir()]
    has_subcategories = len(subdirs) > 3  # 有多个子目录说明是分类根目录

    if has_subcategories:
        print(f"   检测到分类根目录，包含 {len(subdirs)} 个子分类")
        for subdir in sorted(subdirs):
            cat_name = subdir.name
            if category_filter and cat_name != category_filter:
                continue
            categories.append(cat_name)
            files = [f for f in subdir.rglob("*.txt") if f.is_file()]
            for f in files:
                all_books.append((f, cat_name))
    else:
        # 单目录
        cat_name = books_root.name
        categories.append(cat_name)
        files = [f for f in books_root.rglob("*.txt") if f.is_file()]
        for f in files:
            all_books.append((f, cat_name))

    # 抽样限制
    if max_books > 0 and len(all_books) > max_books:
        random.seed(42)
        all_books = random.sample(all_books, max_books)

    print(f"   分类数: {len(categories)}")
    print(f"   书籍数: {len(all_books)}")

    if not all_books:
        print("❌ 没有找到 .txt 文件")
        return

    # 统计
    stats = {
        "total_books": len(all_books),
        "total_categories": len(categories),
        "total_files": len(all_books),
        "encoding_stats": defaultdict(int),
        "chapter_detection_rate": 0,
        "total_chunks": 0,
        "file_sizes": [],
        "books_with_structure": 0,
    }

    print("\n" + "=" * 60)
    print("📖 开始处理...")
    print("=" * 60)

    results = []

    for idx, (file_path, category) in enumerate(all_books):
        rel_path = file_path.relative_to(books_root)
        print(f"\n[{idx+1}/{len(all_books)}] {category}/{file_path.name}")

        book_result = {
            "file": str(rel_path),
            "category": category,
            "status": "pending",
        }

        try:
            # Step 1: 编码检测与读取
            content, encoding = read_with_encoding(str(file_path))
            stats["encoding_stats"][encoding] += 1

            file_size = file_path.stat().st_size
            stats["file_sizes"].append(file_size)

            print(f"   ├─ 编码: {encoding} | 大小: {file_size/1024:.1f}KB | 字符: {len(content)}")

            if len(content) < 10:
                print("   ⚠️  内容过短，跳过")
                book_result["status"] = "skipped (too short)"
                results.append(book_result)
                continue

            # Step 2: 章节检测
            chapters = detect_chapters_regex(content)
            has_structure = len(chapters) > 0

            if has_structure:
                stats["books_with_structure"] += 1
                print(f"   ├─ 章节: 检测到 {len(chapters)} 个章节")
                for ch in chapters[:5]:  # 只显示前5个
                    print(f"   │    [{ch['level']}] {ch['title']}")
                if len(chapters) > 5:
                    print(f"   │    ... 还有 {len(chapters)-5} 个章节")
            else:
                print("   ├─ 章节: 未检测到结构，整体作一个块")

            # Step 3: 分块
            chunks = chunk_by_chapters(content, chapters, str(uuid.uuid4()), category)
            stats["total_chunks"] += len(chunks)

            # 简单的摘要
            summary = generate_book_summary(content[:2000], file_path.stem)

            print(f"   ├─ 分块: {len(chunks)} 个块")
            print(f"   ├─ 摘要: {summary[:80]}...")
            print(f"   └─ 标题: {file_path.stem}")

            # 收集结果
            book_result.update({
                "status": "success",
                "encoding": encoding,
                "size_kb": round(file_size / 1024, 1),
                "total_chars": len(content),
                "chapters_found": len(chapters),
                "has_structure": has_structure,
                "chunks_count": len(chunks),
                "summary": summary,
                "title": file_path.stem,
            })

        except Exception as e:
            print(f"   ❌ 错误: {str(e)}")
            book_result["status"] = f"error: {str(e)}"

        results.append(book_result)

    # ════════════════════════════════════════════════════════
    # 统计报告
    # ════════════════════════════════════════════════════════

    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("📊 构建结果报告")
    print("=" * 60)

    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] != "success" and r["status"] != "skipped (too short)"]

    print(f"\n处理时间: {elapsed:.1f} 秒")
    print(f"处理速度: {len(all_books)/max(elapsed,0.1):.1f} 本/秒")
    print(f"成功: {len(successful)} 本")
    print(f"失败: {len(failed)} 本")
    print(f"总字符: {sum(r.get('total_chars',0) for r in successful):,}")
    print(f"总chunks: {stats['total_chunks']}")
    print(f"章节检测率: {stats['books_with_structure']}/{len(successful)} ({stats['books_with_structure']/max(len(successful),1)*100:.1f}%)")
    print("\n编码分布:")
    for enc, count in sorted(stats["encoding_stats"].items(), key=lambda x: -x[1]):
        print(f"   {enc}: {count} ({count/max(len(all_books),1)*100:.1f}%)")

    if successful:
        avg_size = sum(r.get("size_kb", 0) for r in successful) / len(successful)
        avg_chunks = sum(r.get("chunks_count", 0) for r in successful) / len(successful)
        print(f"\n平均大小: {avg_size:.1f}KB")
        print(f"平均chunks/本: {avg_chunks:.1f}")

    # ════════════════════════════════════════════════════════
    # 保存报告
    # ════════════════════════════════════════════════════════

    report = {
        "config": {
            "books_dir": books_dir,
            "max_books": max_books,
            "category_filter": category_filter,
        },
        "stats": {
            "elapsed_seconds": round(elapsed, 1),
            "total_books": len(all_books),
            "successful": len(successful),
            "failed": len(failed),
            "total_chunks": stats["total_chunks"],
            "books_with_structure": stats["books_with_structure"],
            "structure_detection_rate": round(stats["books_with_structure"] / max(len(successful), 1), 3),
        },
        "encoding_stats": dict(stats["encoding_stats"]),
        "total_categories": len(categories),
        "results": results,
    }

    DEMO_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(DEMO_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n完整报告: {DEMO_OUTPUT}")

    return report


# ════════════════════════════════════════════════════════════
# 入口
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="知识库构建流程 Demo")
    parser.add_argument("--dir", type=str, default=r"C:\Users\huiya\Desktop\books",
                        help="书籍目录路径")
    parser.add_argument("--count", type=int, default=0,
                        help="最大处理数量（0=全部）")
    parser.add_argument("--category", type=str, default=None,
                        help="分类过滤（如：幽默笑话、历史军事）")
    parser.add_argument("--full", action="store_true",
                        help="全量处理所有书籍")

    args = parser.parse_args()

    if args.full:
        args.count = 0

    demo_build_knowledge_base(
        books_dir=args.dir,
        max_books=args.count,
        category_filter=args.category,
    )
