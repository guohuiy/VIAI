"""
书籍数据集特征分析脚本
扫描 books 目录，从每个子目录随机抽4本书，分析文档和内容特征
"""

import os
import sys
import json
import random
import chardet
from pathlib import Path
from collections import defaultdict, Counter

# 书籍根目录
BOOKS_ROOT = Path(r"C:\Users\huiya\Desktop\books")
OUTPUT_FILE = Path(__file__).parent.parent / "runtime" / "books_analysis_report.json"

# 支持的格式
SUPPORTED_EXTS = {".txt", ".pdf", ".doc", ".docx", ".epub", ".mobi"}

def detect_encoding(file_path):
    """检测文件编码"""
    try:
        with open(file_path, "rb") as f:
            raw = f.read(min(1024 * 100, os.path.getsize(file_path)))
        result = chardet.detect(raw)
        return result.get("encoding", "unknown"), result.get("confidence", 0)
    except Exception:
        return "error", 0

def get_txt_head(file_path, max_chars=5000):
    """读取 TXT 文件头部内容"""
    encoding, _ = detect_encoding(file_path)
    if encoding == "unknown" or encoding == "error":
        return "", encoding
    encodings_to_try = [encoding, "utf-8", "gbk", "gb18030", "big5"]
    for enc in encodings_to_try:
        try:
            with open(file_path, "r", encoding=enc, errors="replace") as f:
                return f.read(max_chars), enc
        except:
            continue
    return "", encoding

def get_file_size_str(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/1024/1024:.1f}MB"
    else:
        return f"{size_bytes/1024/1024/1024:.1f}GB"

def detect_chapter_patterns(text):
    """检测章节模式"""
    patterns = {
        "第X章": len([l for l in text.split('\n') if '第' in l and ('章' in l or '节' in l)]),
        "数字序号(1.2.3)": len([l for l in text.split('\n') if l.strip() and l.strip()[0].isdigit() and '.' in l[:5]]),
        "中文序号(一二三)": len([l for l in text.split('\n') if any(k in l[:5] for k in ['一、','二、','三、','四、','五、','六、','七、','八、','九、','十、'])]),
        "括号序号": len([l for l in text.split('\n') if l.strip().startswith('（') and '）' in l[:10]]),
    }
    return patterns

def analyze_book_file(file_path: Path):
    """分析单个书籍文件"""
    result = {
        "path": str(file_path),
        "name": file_path.name,
        "suffix": file_path.suffix.lower(),
        "size_bytes": file_path.stat().st_size,
        "size_str": get_file_size_str(file_path.stat().st_size),
    }

    # 只有txt文件能做深度内容分析
    if file_path.suffix.lower() == ".txt":
        content, encoding = get_txt_head(file_path)
        result["encoding"] = encoding
        result["chars_analyzed"] = len(content) if content else 0
        
        if content:
            lines = content.split('\n')
            result["lines_analyzed"] = len(lines)
            result["avg_line_length"] = round(len(content) / max(len(lines), 1), 1)
            
            # 章节模式检测
            result["chapter_patterns"] = detect_chapter_patterns(content)
            
            # 内容特征
            total_chars = len(content)
            chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            english_chars = sum(1 for c in content if c.isascii() and c.isalpha())
            digit_chars = sum(1 for c in content if c.isdigit())
            punctuation = sum(1 for c in content if c in '，。、；：？！""''（）【】《》—…·.,;:?!\'\"()[]{}')
            
            result["content_stats"] = {
                "total_chars": total_chars,
                "chinese_chars": chinese_chars,
                "chinese_ratio": round(chinese_chars / max(total_chars, 1), 3),
                "english_chars": english_chars,
                "digit_chars": digit_chars,
                "punctuation": punctuation,
            }
            
            # 内容类型判断
            if chinese_chars > 0.8 * total_chars:
                result["content_type"] = "纯中文"
            elif chinese_chars > 0.3 * total_chars:
                result["content_type"] = "中英混合"
            else:
                result["content_type"] = "英文/其他"
            
            # 估计字数
            result["estimated_chars_total"] = result.get("chars_analyzed", 0)
            
            # 表/代码/列表特征
            has_table = any('|' in line and '---' in content for line in lines)
            has_code = any('```' in line or '    ' in line[:4] for line in lines[:100])
            has_list = any(line.strip().startswith(('- ', '* ', '•')) for line in lines[:200])
            
            markers = {
                "contains_table": has_table,
                "contains_code": has_code,
                "contains_list": has_list,
            }
            result["content_markers"] = markers

    return result

def main():
    # 获取所有子目录
    subdirs = sorted([d for d in BOOKS_ROOT.iterdir() if d.is_dir()])
    print(f"发现 {len(subdirs)} 个子目录\n")
    
    all_samples = {}
    all_stats = {
        "total_subdirs": len(subdirs),
        "total_sampled": 0,
        "file_types": Counter(),
        "encodings": Counter(),
        "content_types": Counter(),
        "chapter_pattern_summary": Counter(),
        "size_distribution": Counter(),
    }
    
    for subdir in subdirs:
        dir_name = subdir.name
        print(f"📂 [{dir_name}]")
        
        # 收集所有文件（非目录）
        all_files = []
        for f in subdir.rglob("*"):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                all_files.append(f)
        
        # 收集子目录本身（可能一本书就是一个目录）
        sub_folders = [d for d in subdir.iterdir() if d.is_dir()]
        
        if not all_files:
            print(f"   ⚠️  没有直接文件，有 {len(sub_folders)} 个子目录\n")
            if sub_folders:
                # 从子目录中抽样
                sampled_dirs = random.sample(sub_folders, min(4, len(sub_folders)))
                for sd in sampled_dirs:
                    dir_files = [f for f in sd.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS]
                    if dir_files:
                        chosen = random.choice(dir_files)
                        result = analyze_book_file(chosen)
                        all_samples[f"{dir_name}/{sd.name}/{chosen.name}"] = result
                        all_stats["total_sampled"] += 1
                        _update_stats(all_stats, result)
                        print(f"   📄 {sd.name}/{chosen.name}  ({result['size_str']}, {result.get('content_type','?')})")
            else:
                print(f"   (空目录)")
            continue
        
        # 从当前目录随机抽4本
        sample = random.sample(all_files, min(4, len(all_files)))
        for f in sample:
            result = analyze_book_file(f)
            key = f"{dir_name}/{f.name}" if f.parent == subdir else f"{dir_name}/{f.relative_to(subdir)}"
            all_samples[key] = result
            all_stats["total_sampled"] += 1
            _update_stats(all_stats, result)
            print(f"   📄 {f.name}  ({result['size_str']}, {result.get('encoding','?')}, {result.get('content_type','?')})")
        
        print()

    # 打印统计摘要
    print("=" * 60)
    print("📊 分析统计摘要")
    print("=" * 60)
    print(f"总目录数: {all_stats['total_subdirs']}")
    print(f"抽样总数: {all_stats['total_sampled']}")
    print()
    
    print("文件类型分布:")
    for ext, count in all_stats["file_types"].most_common():
        print(f"   {ext}: {count} ({round(count/all_stats['total_sampled']*100, 1)}%)")
    print()
    
    print("内容编码分布:")
    for enc, count in all_stats["encodings"].most_common(10):
        print(f"   {enc}: {count}")
    print()
    
    print("内容类型分布:")
    for ct, count in all_stats["content_types"].most_common():
        print(f"   {ct}: {count} ({round(count/all_stats['total_sampled']*100, 1)}%)")
    print()
    
    print("文件大小分布:")
    for sz, count in all_stats["size_distribution"].most_common():
        print(f"   {sz}: {count}")
    print()
    
    # 保存详细结果
    output = {
        "stats_summary": {
            "total_subdirs": all_stats["total_subdirs"],
            "total_sampled": all_stats["total_sampled"],
            "file_types": dict(all_stats["file_types"].most_common()),
            "encodings": dict(all_stats["encodings"].most_common()),
            "content_types": dict(all_stats["content_types"].most_common()),
            "size_distribution": dict(all_stats["size_distribution"].most_common()),
        },
        "samples": all_samples,
    }
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    print(f"详细报告已保存到: {OUTPUT_FILE}")

def _update_stats(stats, result):
    stats["file_types"][result["suffix"]] += 1
    
    if "encoding" in result:
        stats["encodings"][result["encoding"]] += 1
    if "content_type" in result:
        stats["content_types"][result["content_type"]] += 1
    
    size = result["size_bytes"]
    if size < 100*1024:
        stats["size_distribution"]["<100KB"] += 1
    elif size < 500*1024:
        stats["size_distribution"]["100KB-500KB"] += 1
    elif size < 1024*1024:
        stats["size_distribution"]["500KB-1MB"] += 1
    elif size < 5*1024*1024:
        stats["size_distribution"]["1MB-5MB"] += 1
    elif size < 10*1024*1024:
        stats["size_distribution"]["5MB-10MB"] += 1
    else:
        stats["size_distribution"][">10MB"] += 1

if __name__ == "__main__":
    main()