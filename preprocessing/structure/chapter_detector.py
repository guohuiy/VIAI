"""
章节识别器
使用多层次正则规则识别电子书章节结构
支持 7 种章节模式 + 可选 Qwen3.5 语义推理
"""

import re
from typing import Any, Dict, List

from core.llm import call_llama_cpp, parse_json_from_response

# 7种章节模式（按优先级从高到低排列）
# 每项: (正则表达式, 层级)
CHAPTER_PATTERNS = [
    # ---- 第1优先级：第X章/第X回（中文古典/现代书籍标准模式） ----
    # "第一章 绪论"  "第1章 基础知识"  "第2回 贾夫人仙逝"
    (r'^\s*(第[一二三四五六七八九十百千万\d]+[章节回部卷篇集]).*$', 1),

    # ---- 第2优先级：Book/Chapter/Section/Part X（英文书籍标准模式） ----
    # "Chapter 1 Introduction"  "Part One"  "Section 2.1"
    (r'^\s*(Book|Chapter|Section|Part|Volume)\s+([\dIVXLC]+)[\.\s:]*(.*)$', 2),

    # ---- 第3优先级：中文数字序号 ----
    # "一、研究背景"  "二、文献综述"  "三、"
    (r'^\s*([一二三四五六七八九十百千万]+)[、\.\s]+(.+)$', 2),

    # ---- 第4优先级：数字编号 ----
    # "1. 引言"  "1.1 背景"  "2.1.1 定义"
    (r'^\s*(\d+(?:\.\d+)*)[\s\.]+(.+)$', 2),

    # ---- 第5优先级：括号序号 ----
    # "（一）研究目的"  "(二) 分析方法"
    (r'^\s*[（\(]([一二三四五六七八九十]+)[）\)]\s*(.*)$', 3),

    # ---- 第6优先级：英文单词序号 ----
    # "Part One"  "Chapter Two"  "Section Three"
    (r'^\s*(Part|Chapter|Section)\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)[\.\s:]*(.*)$', 2),

    # ---- 第7优先级：序言/附录等特殊标记 ----
    # "前言" "序言" "附录" "后记" "参考文献"
    (r'^\s*(前言|序言|引言|绪论|绪言|导论|导言|附录|后记|跋|参考文献|参考书目|致谢|鸣谢)\s*$', 1),
]


def detect_by_regex(text: str) -> List[Dict[str, Any]]:
    """
    使用 7 种正则规则检测章节结构（多重匹配，用第一个匹配上的）

    Args:
        text: 文本内容

    Returns:
        检测到的章节列表
    """
    lines = text.split("\n")
    chapters = []
    matched_titles = set()  # 去重

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # 跳过太短的行（可能是页码、页眉等噪声）
        if len(stripped) < 3:
            continue

        for pattern, default_level in CHAPTER_PATTERNS:
            match = re.match(pattern, stripped)
            if match:
                # 去重：同一标题只记录一次
                title_key = stripped[:30]
                if title_key in matched_titles:
                    break
                matched_titles.add(title_key)

                # 推断层级
                level = _infer_level(stripped, pattern, default_level)

                chapters.append({
                    "level": level,
                    "title": stripped[:100],  # 截断超长标题
                    "start_line": i,
                    "end_line": i + 1,  # 临时，后续修正
                })
                break  # 用第一个匹配到的模式

    # 后处理：设置 end_line 为下一个章节的开始行
    if chapters:
        for i in range(len(chapters) - 1):
            chapters[i]["end_line"] = chapters[i + 1]["start_line"]
        chapters[-1]["end_line"] = len(lines)

    return chapters


def _infer_level(title: str, pattern: str, default: int) -> int:
    """根据匹配的标题和模式推断具体层级"""
    # 部/卷/集 → 0级
    if re.match(r'^第[一二三四五六七八九十百千万\d]+[部卷集]', title):
        return 0
    # 章/回 → 1级
    if re.match(r'^第[一二三四五六七八九十百千万\d]+[章回]', title):
        return 1
    # 节/篇 → 2级
    if re.match(r'^第[一二三四五六七八九十百千万\d]+[节篇]', title):
        return 2
    # 前言/附录等 → 0级
    if re.match(r'^(前言|序言|引言|绪论|附录|后记|跋|参考文献)', title):
        return 0
    # 数字编号：1.1.1 → 3级, 1.1 → 2级, 1. → 2级
    if re.match(r'^\d+\.\d+\.', title):
        return 3
    if re.match(r'^\d+\.', title):
        return 2
    return default


def detect_by_llm(text: str, max_chars: int = 2000) -> List[Dict[str, Any]]:
    """
    使用 Qwen3.5 语义推理识别章节结构
    注意：LLM 推理较慢，仅在 `--analyze` 模式下使用

    Args:
        text: 文本内容（前 max_chars 字符）
        max_chars: 最大输入字符数

    Returns:
        检测到的章节列表
    """
    prompt = f"""分析以下电子书内容，识别其章节结构。
返回格式：
```json
{{
  "title": "书名（如果能在内容中推断）",
  "chapters": [
    {{"level": 1, "title": "第一章 标题", "start_line": 1, "end_line": 50}},
    {{"level": 2, "title": "第一节", "start_line": 3, "end_line": 20}}
  ]
}}
```

电子书内容（前{max_chars}字）：
{text[:max_chars]}
"""
    try:
        response = call_llama_cpp(prompt, max_tokens=1024)
        result = parse_json_from_response(response)
        return result.get("chapters", [])
    except Exception:
        return []


def detect_structure(raw_text: str, use_llm: bool = True) -> Dict[str, Any]:
    """
    多层次章节识别

    流程：
    1. 先尝试 7 种正则模式快速匹配
    2. 如果正则检测到足够章节 → 直接返回
    3. 如果正则结果不足（<2章）且 use_llm=True → 调用 Qwen3.5 补充分析
       （批量导入时 use_llm=False，仅用正则）

    Args:
        raw_text: 原始文本
        use_llm: 是否在正则检测不足时启用 LLM 推理
                 True=单本书深度分析, False=批量导入（建议）

    Returns:
        { "title": str, "chapters": List[Dict] }
    """
    # 1. 正则规则层（7种模式）
    regex_chapters = detect_by_regex(raw_text)

    # 2. 语义推理层（仅在 use_llm=True 且正则结果不足时启用）
    if use_llm and len(regex_chapters) < 2:
        try:
            llm_chapters = detect_by_llm(raw_text)
            if llm_chapters:
                return {
                    "title": _extract_title(raw_text),
                    "chapters": _merge_chapters(llm_chapters),
                }
        except Exception:
            pass

    return {
        "title": _extract_title(raw_text),
        "chapters": _merge_chapters(regex_chapters),
    }


def _extract_title(text: str) -> str:
    """从文本中提取书名"""
    lines = text.strip().split("\n")
    for line in lines[:10]:
        stripped = line.strip().strip("#").strip()
        if stripped and len(stripped) < 50:
            return stripped
    return "未命名书籍"


def _merge_chapters(chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    后处理合并：修正层级关系、合并过小的章节

    Args:
        chapters: 原始章节列表

    Returns:
        处理后的章节列表
    """
    if not chapters:
        return []

    merged = [chapters[0]]
    for ch in chapters[1:]:
        prev = merged[-1]
        # 如果当前章节行号范围过小（<3行），合并到上一章
        if ch["end_line"] - ch["start_line"] < 3:
            prev["end_line"] = ch["end_line"]
        else:
            merged.append(ch)

    return merged
