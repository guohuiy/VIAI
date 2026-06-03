"""
Demo：使用 Qwen3.5-2B 模型进行书籍智能分块测试
对比纯正则分块 vs LLM 分块的效果差异

用法：
  python scripts/demo_llm_chunking.py
  python scripts/demo_llm_chunking.py --count 5
  python scripts/demo_llm_chunking.py --category "历史军事"
"""

import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List

# 确保项目根目录在路径中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ════════════════════════════════════════════════════════════
# 配置
# ════════════════════════════════════════════════════════════

BOOKS_ROOT = Path(r"C:\Users\huiya\Desktop\books")
DEMO_OUTPUT = Path(__file__).parent.parent / "runtime" / "llm_chunking_report.json"

# 从 demo_knowledge_base 导入编码和正则分块函数
sys.path.insert(0, str(Path(__file__).parent))

# 直接复制编码检测函数（避免import循环）
def robust_detect_encoding(file_path: str) -> str:
    """增强版编码检测"""
    CHINESE_ENCODINGS_LIST = ["gb18030", "gbk", "gb2312", "utf-8", "big5", "utf-16"]
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        raw_data = f.read(min(1024 * 100, file_size))
    has_high_bytes = any(0x81 <= raw_data[i] <= 0xFE for i in range(min(len(raw_data), 1000)))
    try:
        import chardet
        detect_result = chardet.detect(raw_data)
        detected_enc = detect_result.get("encoding", "").lower() if detect_result.get("encoding") else ""
        confidence = detect_result.get("confidence", 0)
    except Exception:
        detected_enc = ""
        confidence = 0
    reliable_chinese = {"gb2312", "gbk", "gb18030", "big5", "utf-8", "utf-16", "utf-16le", "utf-16be"}
    if confidence > 0.5 and detected_enc in reliable_chinese:
        if detected_enc in ("gb2312", "gbk"):
            return "gb18030"
        if detected_enc.startswith("utf-16"):
            return "utf-16"
        return detected_enc
    if has_high_bytes:
        for enc in CHINESE_ENCODINGS_LIST:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    f.read(200)
                return enc
            except Exception:
                continue
    if detected_enc and confidence > 0.1:
        return detected_enc
    return "utf-8"

def read_with_encoding(file_path: str) -> tuple:
    encoding = robust_detect_encoding(file_path)
    try:
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            content = f.read()
        return content, encoding
    except Exception:
        with open(file_path, "rb") as f:
            content = f.read().decode("utf-8", errors="replace")
        return content, "utf-8(force)"

# ════════════════════════════════════════════════════════════
# 正则分块（对比基准）
# ════════════════════════════════════════════════════════════

import re  # noqa: E402


def regex_chunking(text: str) -> tuple[List[Dict], List[str]]:
    """纯正则分块，返回 (chunks列表, chunk文本列表)"""
    lines = text.split('\n')
    chapters = []

    patterns = [
        r'^\s*(第[一二三四五六七八九十百千万\d]+[章节回部卷篇集]).*$',
        r'^\s*(Book|Chapter|Section|Part|Volume)\s+([\dIVXLC]+).*$',
        r'^\s*([一二三四五六七八九十百千万]+)[、\.\s]+.+$',
        r'^\s*(\d+(?:\.\d+)*)[\s\.]+.+$',
        r'^\s*[（\(]([一二三四五六七八九十]+)[）\)].*$',
    ]

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        for pat in patterns:
            if re.match(pat, stripped):
                chapters.append({"start": i, "title": stripped[:50]})
                break

    if not chapters:
        return [{"start": 0, "end": len(lines), "title": "全文"}], [text[:5000]]

    for i in range(len(chapters) - 1):
        chapters[i]["end"] = chapters[i+1]["start"]
    chapters[-1]["end"] = len(lines)

    chunks = []
    chunk_texts = []
    for ch in chapters:
        ct = '\n'.join(lines[ch["start"]:ch["end"]]).strip()
        if ct:
            chunks.append(ch)
            chunk_texts.append(ct)

    return chunks, chunk_texts


# ════════════════════════════════════════════════════════════
# LLM 分块
# ════════════════════════════════════════════════════════════

def llm_analyze_structure(text: str, title: str, max_context_chars: int = 3000) -> dict:
    """
    使用 Qwen3.5-2B 分析书籍结构，返回章节/分块建议

    由于 2B 模型上下文限制（8K tokens ≈ 4000-5000 中文字符），
    对长文本只分析开头部分来识别结构
    """
    from core.llm import call_llama_cpp

    # 取文本开头部分（题目+目录+前几段）
    preview = text[:max_context_chars]

    prompt = f"""你是一个专业的书籍结构分析师。请分析下面这本书的开头内容，识别其章节结构和自然分块边界。

## 书名
{title}

## 书籍开头内容
{preview}

## 分析任务
1. 这本书是否有明确的章节结构？（如 第X章、一、二、三、1.1、Part 1 等）
2. 如果有，列出检测到的章节标题
3. 建议在哪里切分最合理（自然段落边界、主题转换处）

## 输出格式（JSON）
```json
{{
  "has_structure": true/false,
  "structure_type": "章/节/数字序号/无结构",
  "chapters": [
    {{"title": "第一章 标题", "line_marker": "第一章"}},
    {{"title": "第二章 标题", "line_marker": "第二章"}}
  ],
  "suggested_chunks": 5,
  "analysis": "简短分析，这本书的内容组织方式是..."
}}
```

请严格按照 JSON 格式输出，不要输出额外内容。"""

    try:
        print("     ⏳ 正在调用 Qwen3.5-2B 分析结构...", end=" ")
        sys.stdout.flush()

        response = call_llama_cpp(
            prompt=prompt,
            max_tokens=512,
            temperature=0.1,  # 低温度保一致性
            timeout=120,
        )
        print("done")

        # 解析 JSON
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {"has_structure": False, "error": "LLM返回非JSON格式", "raw": response[:200]}

    except Exception as e:
        print(f"❌ LLM调用失败: {str(e)[:80]}")
        return {"has_structure": False, "error": str(e)}


def llm_chunking(text: str, llm_result: dict, title: str) -> tuple[List[Dict], List[str]]:
    """基于 LLM 分析结果进行分块"""
    lines = text.split('\n')
    chunks = []
    chunk_texts = []

    if not llm_result.get("has_structure"):
        # LLM认为无结构，按段落大小分块
        chunk_size = 2000
        for i in range(0, len(text), chunk_size):
            ct = text[i:i+chunk_size]
            if ct.strip():
                chunks.append({"start": i, "end": i+len(ct), "title": f"段落{len(chunks)+1}"})
                chunk_texts.append(ct)
        return chunks, chunk_texts

    # LLM识别出了结构，按章节边界分块
    chapters = llm_result.get("chapters", [])
    chapter_markers = [ch.get("line_marker", "") for ch in chapters]

    if not chapter_markers:
        # 有结构但没能提取出具体章节标记，估算分块数
        suggested = llm_result.get("suggested_chunks", 5)
        chunk_size = max(len(text) // suggested, 1000)
        for i in range(0, len(text), chunk_size):
            ct = text[i:i+chunk_size]
            if ct.strip():
                chunks.append({"start": i, "end": i+len(ct), "title": f"节{len(chunks)+1}"})
                chunk_texts.append(ct)
        return chunks, chunk_texts

    # 在lines中查找章节标记位置
    boundaries = []
    for i, line in enumerate(lines):
        for marker in chapter_markers:
            if marker and marker in line:
                boundaries.append(i)
                break

    boundaries = sorted(set(boundaries))

    if not boundaries:
        # 找不到精确位置，均分
        suggested = max(len(chapter_markers), 3)
        chunk_size = len(text) // suggested
        for i in range(0, len(text), chunk_size):
            ct = text[i:i+chunk_size]
            if ct.strip():
                chunks.append({"start": i, "end": i+len(ct), "title": f"段{len(chunks)+1}"})
                chunk_texts.append(ct)
        return chunks, chunk_texts

    # 在边界处分块
    boundaries = [0] + boundaries + [len(lines)]
    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i+1]
        ct = '\n'.join(lines[start:end]).strip()
        if ct:
            marker_text = chapter_markers[i] if i < len(chapter_markers) else f"节{i}"
            chunks.append({"start": start, "title": marker_text})
            chunk_texts.append(ct[:3000])  # 限制单块最大3000字符

    return chunks, chunk_texts


# ════════════════════════════════════════════════════════════
# 分块质量评估
# ════════════════════════════════════════════════════════════

def evaluate_chunk_quality(text: str, chunks: List[Dict], chunk_texts: List[str]) -> Dict:
    """评估分块质量"""
    if not chunk_texts:
        return {"score": 0, "issues": ["无分块"]}

    # 1. 块大小一致性（好的分块应该大小相近）
    sizes = [len(ct) for ct in chunk_texts]
    avg_size = sum(sizes) / len(sizes) if sizes else 0
    size_std = (sum((s - avg_size)**2 for s in sizes) / len(sizes))**0.5 if len(sizes) > 1 else 0
    consistency = max(0, 1 - size_std / max(avg_size, 1))

    # 2. 覆盖度（分块是否覆盖了大部分内容）
    total_chunked = sum(sizes)
    coverage = min(1.0, total_chunked / max(len(text), 1))

    # 3. 块数量是否合理
    chunk_count_score = min(1.0, len(chunks) / max(len(text) / 1000, 1))

    # 4. 是否有过小或过大的块
    too_small = sum(1 for s in sizes if s < 100)
    too_large = sum(1 for s in sizes if s > 5000)
    size_issues = too_small + too_large

    score = (consistency * 0.3 + coverage * 0.3 + chunk_count_score * 0.2 +
             max(0, 1 - size_issues / max(len(chunks), 1)) * 0.2)

    issues = []
    if too_small > 0:
        issues.append(f"{too_small}个过小块(<100字符)")
    if too_large > 0:
        issues.append(f"{too_large}个超大块(>5000字符)")
    if consistency < 0.5:
        issues.append("块大小差异大")

    return {
        "score": round(score, 3),
        "chunks_count": len(chunks),
        "avg_chunk_size": round(avg_size, 0),
        "size_std": round(size_std, 0),
        "consistency": round(consistency, 3),
        "coverage": round(coverage, 3),
        "issues": issues,
    }


# ════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Qwen3.5-2B LLM分块效果测试")
    parser.add_argument("--count", type=int, default=8, help="测试书籍数量")
    parser.add_argument("--category", type=str, default=None, help="分类过滤")
    args = parser.parse_args()

    print("=" * 70)
    print("🤖 LLM 分块效果测试 Demo (Qwen3.5-2B)")
    print("=" * 70)
    print()

    # 收集书籍
    all_books = []
    subdirs = [d for d in BOOKS_ROOT.iterdir() if d.is_dir()]

    for subdir in sorted(subdirs):
        cat_name = subdir.name
        if args.category and cat_name != args.category:
            continue
        # 每个分类挑一些书
        files = [f for f in subdir.rglob("*.txt") if f.is_file()]
        # 过滤掉太小的文件（<1KB 可能是片段）
        files = [f for f in files if f.stat().st_size > 1000]
        # 再过滤掉太大的文件（>500KB 超出LLM上下文）
        files = [f for f in files if f.stat().st_size < 500 * 1024]
        # 每个目录取一些
        sample = random.sample(files, min(2, len(files)))
        for f in sample:
            all_books.append((f, cat_name))

    # 限制总数量
    if len(all_books) > args.count:
        random.seed(42)
        all_books = random.sample(all_books, args.count)

    print(f"共 {len(all_books)} 本书参与测试\n")

    results = []
    stats = {
        "total": len(all_books),
        "llm_success": 0,
        "llm_fail": 0,
        "total_time_regex": 0,
        "total_time_llm": 0,
    }

    for idx, (file_path, category) in enumerate(all_books):
        print(f"[{idx+1}/{len(all_books)}] {category}/{file_path.name}")

        content, encoding = read_with_encoding(str(file_path))
        file_size = file_path.stat().st_size
        title = file_path.stem

        print(f"   ├─ 大小: {file_size/1024:.1f}KB | 字符: {len(content)} | 编码: {encoding}")

        # ═══ 正则分块 ═══
        t0 = time.time()
        regex_chunks, regex_texts = regex_chunking(content)
        t1 = time.time()
        regex_time = t1 - t0
        regex_quality = evaluate_chunk_quality(content, regex_chunks, regex_texts)
        stats["total_time_regex"] += regex_time

        print(f"   ├─ 正则分块: {len(regex_chunks)}块 | {regex_time:.2f}s | 质量分:{regex_quality['score']}")

        # ═══ LLM 分块 ═══
        t2 = time.time()
        llm_result = llm_analyze_structure(content, title)
        t3 = time.time()
        llm_time = t3 - t2

        if llm_result.get("error"):
            stats["llm_fail"] += 1
            print(f"   ├─ LLM分块: ❌ 失败 - {llm_result.get('error')[:60]}")
            llm_chunks, llm_texts = [], []
            llm_quality = {"score": 0, "chunks_count": 0, "issues": ["LLM失败"]}
        else:
            stats["llm_success"] += 1
            stats["total_time_llm"] += llm_time

            llm_chunks, llm_texts = llm_chunking(content, llm_result, title)
            llm_quality = evaluate_chunk_quality(content, llm_chunks, llm_texts)

            print(f"   ├─ LLM分块:   {len(llm_chunks)}块 | {llm_time:.2f}s | 质量分:{llm_quality['score']}")
            print(f"   ├─ LLM分析:   有结构={llm_result.get('has_structure')} | 类型={llm_result.get('structure_type','?')}")
            print(f"   └─ 章节数:     {len(llm_result.get('chapters',[]))}")

            # 输出 LLM 分析摘要
            analysis = llm_result.get("analysis", "")
            if analysis:
                print(f"     分析: {analysis[:100]}")

        result = {
            "file": f"{category}/{file_path.name}",
            "title": title,
            "size_kb": round(file_size/1024, 1),
            "chars": len(content),
            "encoding": encoding,
            "regex": {
                "chunks": len(regex_chunks),
                "time_s": round(regex_time, 3),
                "quality": regex_quality,
            },
            "llm": {
                "success": not llm_result.get("error"),
                "chunks": len(llm_chunks) if not llm_result.get("error") else 0,
                "time_s": round(llm_time, 3),
                "quality": llm_quality,
                "analysis": llm_result,
            },
        }
        results.append(result)
        print()

    # ═══════════════════════════════════════
    # 汇总报告
    # ═══════════════════════════════════════

    print("=" * 70)
    print("📊 汇总报告")
    print("=" * 70)

    successful_llm = [r for r in results if r["llm"]["success"]]
    failed_llm = [r for r in results if not r["llm"]["success"]]

    print(f"\n总测试书籍: {len(results)}")
    print(f"LLM成功: {len(successful_llm)}")
    print(f"LLM失败: {len(failed_llm)}")

    if successful_llm:
        avg_regex_time = sum(r["regex"]["time_s"] for r in successful_llm) / len(successful_llm)
        avg_llm_time = sum(r["llm"]["time_s"] for r in successful_llm) / len(successful_llm)

        avg_regex_quality = sum(r["regex"]["quality"]["score"] for r in successful_llm) / len(successful_llm)
        avg_llm_quality = sum(r["llm"]["quality"]["score"] for r in successful_llm) / len(successful_llm)

        avg_regex_chunks = sum(r["regex"]["chunks"] for r in successful_llm) / len(successful_llm)
        avg_llm_chunks = sum(r["llm"]["chunks"] for r in successful_llm) / len(successful_llm)

        print("\n⏱️  性能对比:")
        print(f"  正则分块: 平均 {avg_regex_time:.3f}s/本 (总 {stats['total_time_regex']:.2f}s)")
        print(f"  LLM分块:  平均 {avg_llm_time:.2f}s/本 (总 {stats['total_time_llm']:.2f}s)")
        print(f"  LLM比正则慢: {avg_llm_time/max(avg_regex_time,0.001):.0f} 倍")

        print("\n📐 分块数对比:")
        print(f"  正则: 平均 {avg_regex_chunks:.1f} 块/本")
        print(f"  LLM:  平均 {avg_llm_chunks:.1f} 块/本")

        print("\n⭐ 质量分对比:")
        print(f"  正则: {avg_regex_quality:.3f}")
        print(f"  LLM:  {avg_llm_quality:.3f}")

        better_count = sum(1 for r in successful_llm if r["llm"]["quality"]["score"] > r["regex"]["quality"]["score"])
        worse_count = sum(1 for r in successful_llm if r["llm"]["quality"]["score"] < r["regex"]["quality"]["score"])
        print(f"\n  LLM优于正则: {better_count} 本")
        print(f"  LLM劣于正则: {worse_count} 本")
        print(f"  两者相当: {len(successful_llm) - better_count - worse_count} 本")

    if failed_llm:
        print("\n❌ LLM失败详情:")
        for r in failed_llm:
            err = r["llm"]["analysis"].get("error", "未知错误")
            print(f"  {r['file']}: {err}")

    # 保存报告
    report = {
        "config": {"count": args.count, "category": args.category},
        "summary": {
            "total": len(results),
            "llm_success": len(successful_llm),
            "llm_fail": len(failed_llm),
        },
        "results": results,
    }

    DEMO_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(DEMO_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n完整报告: {DEMO_OUTPUT}")


if __name__ == "__main__":
    main()
