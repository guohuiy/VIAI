# 📚 ebook-content-studio — 私有电子书内容生成系统

> 版本：v1.0 | 日期：2026-05-27 | 基于 live-content-studio 模式重构
> 引擎：Qwen3.5（本地大模型） + llama.cpp（推理引擎）

---

## 一、项目概述

**目标：** 基于用户私有的 TXT/PDF 电子书数据，构建一个全本地化、隐私安全的智能内容生成平台。系统自动分析用户需求、检索电子书内容、生成符合指定主题/风格/字数的脚本。

**核心理念：**
```
用户需求（主题/风格/字数）
        ↓
[需求分析] → 拆解为子主题 + 素材需求清单
        ↓
[素材检索] → 从私有电子书库中 RAG 检索相关内容
        ↓
[脚本生成] → 基于素材 + 需求生成完整脚本
        ↓
   "基于你的书库，为你定制的内容" 📖
```

**核心特点：** 所有数据不出本地，Qwen3.5 驱动全流程，纯 Python 无外部 API 依赖。

---

## 二、系统架构

```
┌────────────────────────────────────────────────────────────┐
│                    应用层 (Application Layer)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  需求解析模块  │  │  生成编排模块  │  │  脚本输出模块    │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                 智能层 (AI Engine Layer)                    │
│     ┌──────────────────────────────────────────┐          │
│     │        Qwen3.5 (本地大模型)               │          │
│     │  ┌─────────┐  ┌─────────┐  ┌─────────┐ │          │
│     │  │需求分析  │  │素材规划  │  │脚本生成  │ │          │
│     │  │ Agent   │  │ Agent   │  │ Agent   │ │          │
│     │  └─────────┘  └─────────┘  └─────────┘ │          │
│     └──────────────────┬───────────────────────┘          │
│                         │                                   │
│        llama.cpp (推理引擎 — 编译好的可执行文件)              │
│        qwen3.5-14b-Q4_K_M.gguf (模型文件)                   │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                 检索层 (Retrieval Layer)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  混合检索引擎 │  │  重排序模块  │  │  上下文组装模块  │ │
│  │  (向量+BM25) │  │  (LLM重排)  │  │                  │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                  数据层 (Data Layer)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  ChromaDB    │  │  SQLite      │  │  JSON索引       │ │
│  │  (向量数据库)  │  │  (结构化存储) │  │  (元数据索引)   │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                预处理层 (Preprocessing Layer)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  文档解析器  │  │  结构重建器  │  │  语义分块器     │ │
│  │  (PyMuPDF)  │  │  (章节识别)  │  │  (embedding分块) │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

---

## 三、核心依赖与技术栈

| 组件 | 用途 | 选型 | 说明 |
|------|------|------|------|
| **大模型** | Agent 推理 + 生成 | **Qwen3.5-14B** | GGUF 量化版，本地运行 |
| **推理引擎** | 模型加载与推理 | **llama.cpp** | 编译好的可执行文件 `llama-cli.exe` |
| **嵌入模型** | 文本向量化 | **BGE-M3 ** | 通过 llama.cpp embedding 接口 |
| **向量数据库** | 语义检索 | **ChromaDB** | 纯 Python 本地库，无外部依赖 |
| **文档解析** | PDF/TXT 读取 | **PyMuPDF (fitz)** + 内置编码检测 | 轻量级解析 |
| **全文检索** | 关键词匹配 | **SQLite FTS5** | 内置全文索引 |
| **结构化存储** | 元数据管理 | **SQLite** | 零配置本地存储 |
| **TTS 语音** | 配音（可选） | **edge-tts** （复用 live-content-studio） | 可选模块 |

---

## 四、核心模块详细设计

### 4.1 预处理层

#### 4.1.1 文档解析器（Document Parser）

| 文件类型 | 解析方式 | 输出 |
|----------|---------|------|
| **TXT** | 自动检测编码（UTF-8/GBK/GB2312），按换行分段落 | 原始文本 + 段落列表 |
| **PDF（文本版）** | PyMuPDF 提取文本 + 字体/位置信息 | 文本 + 排版元数据 |
| **PDF（扫描版）** | PaddleOCR（可选） | 文本 + 坐标 |

```
输入: 电子书文件 (.txt / .pdf)
  │
  ▼
┌─ 格式识别 ────────────────────┐
│  TXT → 编码检测 → utf-8 文本  │
│  PDF → PyMuPDF → 逐页提取文本  │
│        ├─ 保留字体大小/样式     │
│        └─ 保留位置坐标          │
└──────────────┬────────────────┘
               ▼
输出: {
  "pages": [{"text": "...", "fonts": [...], "blocks": [...]}],
  "encoding": "utf-8",
  "total_chars": 152400
}
```

#### 4.1.2 结构重建器（Structure Reconstructor）

通过 Qwen3.5 （llama.cpp）识别章节结构：

```python
def detect_structure(raw_text: str) -> dict:
    """
    使用 Qwen3.5 识别电子书结构
    调用 llama.cpp 进行推理
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

电子书内容（前2000字）：
{raw_text[:2000]}
"""
    response = call_llama_cpp(prompt, model="qwen3.5", max_tokens=1024)
    return parse_json_from_response(response)
```

**章节识别的层次化规则：**
1. **正则规则层** — 先匹配 `第X章` / `第X节` / `一、` / `1.1` 等模式
2. **语义推理层** — Qwen3.5 判断是否可能是章节标题（居中、字体突变等）
3. **后处理合并** — 合并过小的章节，修正层级关系

#### 4.1.3 语义分块器（Semantic Chunker）

多层次混合分块策略：

| 策略 | 条件 | 方式 |
|------|------|------|
| **结构分块** | 有明确的章节边界 | 按章节/节边界切分 |
| **语义分块** | 段落边界不清 | 利用嵌入模型计算段落间相似度，动态分块 |
| **固定分块** | 超长连续文本 | 512 token 滑动窗口 + 128 token 重叠 |
| **递归分块** | 分块后仍有超长块 | 递归切分至目标大小 |

输出分块元数据：
```python
{
    "chunk_id": "uuid",
    "book_id": "uuid",
    "struct_path": "book_id/chapter_2/section_1",
    "content": "文本内容...",
    "token_count": 512,
    "embedding": [0.123, -0.456, ...],  # bge-m3 embedding via llama.cpp
    "start_char": 1024,
    "end_char": 2048,
    "heading_stack": ["第一章", "第一节"]
}
```

---

### 4.2 数据层

#### 4.2.1 向量数据库 — ChromaDB

```python
import chromadb

client = chromadb.PersistentClient(path="./data/vector_db")
collection = client.get_or_create_collection(
    name="book_chunks",
    metadata={"hnsw:space": "cosine"}
)

# 存储分块
collection.add(
    ids=["chunk_uuid"],
    embeddings=[[0.123, -0.456, ...]],  # 通过 llama.cpp embedding 生成
    documents=["原始文本内容"],
    metadatas=[{
        "book_id": "book_uuid",
        "struct_path": "book_id/chapter_2",
        "token_count": 512,
        "heading": "第一章",
    }]
)
```

**为什么选 ChromaDB 而非 Milvus/Qdrant：**
- 纯本地运行，无需启动独立服务
- 自动持久化到磁盘文件
- Python 导入即用，零配置
- 支持 HNSW 索引，性能满足百万级分块

#### 4.2.2 结构化存储 — SQLite

核心表设计：

```sql
-- 书籍表
CREATE TABLE books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    file_path TEXT NOT NULL,
    total_chars INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    embedding_model TEXT DEFAULT 'bge-m3',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 章节表
CREATE TABLE chapters (
    id TEXT PRIMARY KEY,
    book_id TEXT REFERENCES books(id),
    parent_id TEXT REFERENCES chapters(id),
    level INTEGER DEFAULT 1,
    title TEXT NOT NULL,
    start_char INTEGER DEFAULT 0,
    end_char INTEGER DEFAULT 0,
    summary TEXT DEFAULT '',
    chunk_ids TEXT DEFAULT '[]'
);

-- 全文索引
CREATE VIRTUAL TABLE fts_chunks USING fts5(
    chunk_id, content,
    tokenize='unicode61'
);
```

#### 4.2.3 元数据索引

| 索引类型 | 实现方式 | 用途 |
|----------|---------|------|
| 全文索引FTS5 | SQLite FTS5 | 关键词搜索 |
| 标签索引 | 额外 `chunk_tags` 表 | 按主题分类筛选 |
| 结构路径索引 | B-tree on `struct_path` | 按章节范围筛选 |

---

### 4.3 检索层（Retrieval Layer）

#### 4.3.1 混合检索引擎

```
用户查询
    │
    ├─→ 向量检索 (ChromaDB) ──┐
    │   嵌入: llama.cpp embedding    │
    │   Top-K: 50                │
    │                            │
    ├─→ 全文检索 (FTS5) ──────┤→ RRF融合 → Top-K → 重排序
    │   SQLite FTS5            │
    │   使用关键词匹配          │
    │                            │
    └─→ 结构化筛选 ──────────┘
        按书籍/章节/标签过滤
```

**RRF 融合算法：**
```python
def rrf_fusion(vector_results, fts_results, k=60):
    """Reciprocal Rank Fusion"""
    scores = {}
    for rank, doc_id in enumerate(vector_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    for rank, doc_id in enumerate(fts_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: -x[1])[:20]
```

#### 4.3.2 重排序模块

使用 Qwen3.5 对候选结果进行相关性判断：

```python
def llm_rerank(query, candidates):
    prompt = f"""判断以下素材与查询的相关性，从高到低排序。
查询：{query}

素材列表：
{chr(10).join(f"[{i}] {c['content'][:200]}" for i, c in enumerate(candidates))}

请输出排序后的序号列表（最相关在前），格式：[3, 0, 1, 2]
"""
    response = call_llama_cpp(prompt, max_tokens=200)
    indices = parse_int_list(response)
    return [candidates[i] for i in indices if i < len(candidates)]
```

#### 4.3.3 上下文组装模块

```python
def assemble_context(retrieved_chunks, max_tokens=4096):
    """
    将检索结果组装成 LLM 可用的上下文
    """
    context_parts = []
    total_tokens = 0
    
    # 按原文顺序排列（保持逻辑连贯）
    sorted_chunks = sorted(retrieved_chunks, key=lambda c: c['start_char'])
    
    for chunk in sorted_chunks:
        block = f"""## 素材 [{len(context_parts)+1}]
**来源**：《{chunk['book_title']}》{chunk['heading']}
**相关性**：{chunk['relevance']:.2f}
**内容**：{chunk['content']}
"""
        tokens = estimate_tokens(block)
        if total_tokens + tokens > max_tokens:
            break
        context_parts.append(block)
        total_tokens += tokens
    
    return '\n'.join(context_parts)
```

---

### 4.4 智能层（AI Engine Layer）— Qwen3.5 驱动

#### 4.4.1 llama.cpp 调用封装

```python
import subprocess
import json

LLAMA_CLI = "C:/tools/llama.cpp/build/bin/llama-cli.exe"
MODEL_PATH = "C:/models/qwen3.5-14b-Q4_K_M.gguf"
LLAMA_EMBED = "C:/tools/llama.cpp/build/bin/llama-embedding.exe"
EMBED_MODEL = "C:/models/bge-m3-Q4_K_M.gguf"


def call_llama_cpp(prompt: str, max_tokens: int = 2048, temperature: float = 0.7) -> str:
    """
    调用 llama.cpp 运行 Qwen3.5 模型
    """
    # 将 prompt 写入临时文件（避免命令行长度限制）
    prompt_file = "runtime/_prompt.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    result = subprocess.run([
        LLAMA_CLI,
        '-m', MODEL_PATH,
        '-f', prompt_file,
        '--temp', str(temperature),
        '-n', str(max_tokens),
        '-c', '8192',         # 上下文窗口
        '--repeat-penalty', '1.1',
        '--no-display-prompt',  # 不输出 prompt
    ], capture_output=True, text=True, timeout=300)

    return result.stdout.strip()


def get_embedding(text: str) -> list[float]:
    """
    通过 llama.cpp embedding 接口生成向量
    """
    result = subprocess.run([
        LLAMA_EMBED,
        '-m', EMBED_MODEL,
        '-p', text,
    ], capture_output=True, text=True, timeout=60)

    return json.loads(result.stdout.strip())
```

#### 4.4.2 需求分析 Agent（Requirement Analysis Agent）

```python
def requirement_analysis(theme, style, word_count, audience):
    prompt = f"""你是一个专业的内容需求分析师。请分析以下生成需求。

## 输入参数
- 主题：{theme}
- 风格：{style}
- 目标字数：{word_count}
- 受众：{audience}

## 任务
1. 将主题拆解为 3~6 个子主题
2. 为每个子主题生成素材检索查询（2~3 个查询词）
3. 确定语言风格特征
4. 输出 JSON 格式

## 输出格式
```json
{{
  "core_theme": "...",
  "sub_themes": ["...", "..."],
  "style_profile": {{"tone": "...", "language": "...", "narrative": "..."}},
  "material_queries": [{{"topic": "...", "queries": ["...", "..."]}}],
  "estimated_sections": 5,
  "target_word_count": 3000
}}
```
"""
    response = call_llama_cpp(prompt, max_tokens=1024)
    return json.loads(parse_json_from_response(response))
```

#### 4.4.3 素材规划 Agent（Material Planning Agent）

```python
def material_planning(analysis_result):
    """
    1. 为每个子主题生成检索查询
    2. 调用混合检索获取素材
    3. 评估素材覆盖度
    4. 识别素材缺口
    """
    material_plan = []
    for sub_theme in analysis_result['sub_themes']:
        # 生成查询
        queries = [
            sub_theme,
            f"{sub_theme} 定义 概念",
            f"{sub_theme} 案例 例子",
            f"{sub_theme} 历史 背景",
        ]
        
        # 混合检索
        all_results = []
        for q in queries:
            vector_results = vector_search(q, top_k=10)
            fts_results = fts_search(q, top_k=10)
            all_results.extend(rrf_fusion(vector_results, fts_results))
        
        # 去重 + LLM重排
        top_chunks = llm_rerank(sub_theme, deduplicate(all_results))[:5]
        
        material_plan.append({
            "sub_theme": sub_theme,
            "queries": queries,
            "retrieved_chunks": [c['chunk_id'] for c in top_chunks],
            "coverage": "adequate" if len(top_chunks) >= 3 else "insufficient",
            "gaps": [] if len(top_chunks) >= 3 else ["需要更多素材"]
        })
    
    return material_plan
```

#### 4.4.4 脚本生成 Agent（Script Generation Agent）

三段式生成策略：

**A. 大纲生成**
```python
def generate_outline(analysis, material_context):
    prompt = f"""基于以下素材和需求，生成一个{analysis['style_profile']['tone']}风格的脚本大纲。

## 主题
{analysis['core_theme']}

## 素材内容
{material_context}

## 要求
- 总字数约{analysis['target_word_count']}字
- 包含{analysis['estimated_sections']}个主要部分
- 每部分标注核心素材来源

请输出 Markdown 格式的脚本大纲。
"""
    return call_llama_cpp(prompt, max_tokens=2048)
```

**B. 分段生成（迭代）**
```python
def generate_section(section_num, section_title, material, style_profile, word_count):
    prompt = f"""请基于以下素材，生成脚本的第{section_num}部分「{section_title}」。

## 风格要求
- 语调：{style_profile['tone']}
- 语言：{style_profile['language']}
- 叙事方式：{style_profile['narrative']}

## 字数要求
约{word_count}字

## 素材内容
{material}

## 注意事项
1. 自然融入素材，不要生硬堆砌
2. 保持叙事连贯性
3. 引用原文观点时标注来源
"""
    return call_llama_cpp(prompt, max_tokens=4096)
```

**C. 后处理**
```python
def post_process(full_script, target_word_count):
    prompt = f"""请对以下脚本进行后处理：

## 任务
1. 检查并校准字数（目标：{target_word_count}字）
2. 统一语言风格
3. 规范化所有引用标注
4. 修复任何前后不一致

## 脚本内容
{full_script}

请输出修正后的完整脚本。
"""
    return call_llama_cpp(prompt, max_tokens=4096)
```

---

### 4.5 应用层

#### 4.5.1 命令行入口（类似 build_today.py）

```bash
# 一键生成
python generate.py "人工智能发展简史" --style 科普 --words 3000

# 交互模式（逐步骤确认）
python generate.py "量子计算入门" --interactive

# 仅素材检索预览
python generate.py "深度学习" --step material --show-sources
```

#### 4.5.2 生成编排流程

```
开始
  │
  ▼
[需求分析 Agent → Qwen3.5] ─── 拆解主题、生成查询
  │                                  │
  ▼                                  ▼
[素材规划] ──── 混合检索 → 评估覆盖度
  │                                  │
  ├─ 素材充足 ──→ 继续              │
  └─ 素材不足 ──→ 提示用户          │
  │                                  │
  ▼                                  ▼
[大纲生成 → Qwen3.5] ─── 输出大纲
  │                                  │
  ├─ 用户确认（交互模式）           │
  │                                  │
  ▼                                  ▼
[分段生成 → Qwen3.5] ─── 逐段生成
  │                                  │
  ▼                                  ▼
[后处理 → Qwen3.5] ─── 字数/风格/引用
  │                                  │
  ▼
[输出脚本] ─── Markdown 文件
```

---

## 五、项目目录结构

```
ebook-content-studio/
│
├── core/                          ← 核心引擎
│   ├── __init__.py
│   ├── llm.py                     # llama.cpp 调用封装
│   ├── embedding.py               # 向量生成接口
│   └── config.py                  # 全局配置（模型路径、参数）
│
├── preprocessing/                 ← 预处理层
│   ├── __init__.py
│   ├── parsers/
│   │   ├── base.py                # 解析器基类
│   │   ├── txt_parser.py          # TXT 解析
│   │   └── pdf_parser.py          # PDF 解析 (PyMuPDF)
│   ├── structure/
│   │   ├── chapter_detector.py    # 章节识别（正则+Qwen3.5）
│   │   └── tree_builder.py        # 结构树构建
│   └── chunking/
│       ├── semantic_chunker.py    # 语义分块
│       ├── fixed_chunker.py       # 固定大小分块
│       └── recursive_chunker.py   # 递归分块
│
├── retrieval/                     ← 检索层
│   ├── __init__.py
│   ├── vector_store.py            # ChromaDB 操作
│   ├── fulltext_engine.py         # SQLite FTS5 全文检索
│   ├── hybrid_retriever.py        # 混合检索（RRF融合）
│   ├── reranker.py                # Qwen3.5 重排序
│   └── context_assembler.py       # 上下文组装
│
├── agents/                        ← 智能层
│   ├── __init__.py
│   ├── base.py                    # Agent 基类
│   ├── requirement_agent.py       # 需求分析 Agent
│   ├── material_agent.py          # 素材规划 Agent
│   └── generation_agent.py        # 脚本生成 Agent
│
├── services/                      ← 业务服务
│   ├── __init__.py
│   ├── book_service.py            # 书籍入库服务
│   └── generation_service.py      # 生成编排服务
│
├── storage/                       ← 数据层
│   ├── __init__.py
│   ├── schema.sql                 # SQLite 建表语句
│   └── db.py                      # 数据库连接与操作
│
├── scripts/                       ← 工具脚本
│   ├── import_book.py             # 批量导入电子书
│   └── build_index.py             # 重建索引
│
├── generate.py                    ← 主入口（命令行工具）
│
├── data/                          ← 数据目录
│   ├── raw_books/                 # 原始电子书
│   ├── processed/                 # 处理后结构化数据
│   ├── vector_db/                 # ChromaDB 持久化文件
│   └── library.db                 # SQLite 数据库文件
│
├── models/                        ← 模型文件（用户自行下载）
│   ├── qwen3.5-14b-Q4_K_M.gguf   # Qwen3.5 量化模型
│   └── bge-m3-Q4_K_M.gguf        # 嵌入模型
│
├── runtime/                       ← 运行时状态
│   └── workflow-state.yaml        # 工作流状态跟踪
│
├── output/                        ← 生成结果
│   └── YYYY-MM-DD-主题名.md
│
├── config/
│   └── default.yaml               # 默认配置
│
├── requirements.txt               # Python 依赖
└── README.md                      # 项目说明
```

---

## 六、数据处理流水线

### 6.1 电子书入库流程

```
用户将电子书放入 data/raw_books/
  │
  ▼
[格式检测] ─── .txt / .pdf
  │
  ▼
[文档解析] ─── PyMuPDF / txt_parser → 原始文本
  │
  ▼
[文本清洗] ─── 去除页眉页脚/乱码/空白行
  │
  ▼
[章节识别] ─── qwen3.5 分析结构 → 生成章节树
  │
  ▼
[语义分块] ─── 多层次分块 → 生成 Chunk
  │
  ├──→ [向量化] llama.cpp embedding → ChromaDB
  ├──→ [全文索引] → SQLite FTS5
  └──→ [结构化存储] → SQLite books/chapters
  │
  ▼
[入库完成] ─── 输出处理报告
```

### 6.2 内容生成流程

```
用户运行: python generate.py "主题名" --style 科普 --words 3000
  │
  ▼
Step 1: [需求分析 Agent → Qwen3.5]
        拆解主题 → 子主题列表 → 检索查询
  │
  ▼
Step 2: [混合检索]
        向量检索 (ChromaDB) + 全文检索 (FTS5) → RRF融合
        重排序 (Qwen3.5) → Top-K 结果
  │
  ▼
Step 3: [上下文组装]
        按原文顺序排列 → 标注来源 → 长度裁剪
  │
  ▼
Step 4: [脚本生成 → Qwen3.5]
        大纲生成 → 分段生成 → 后处理
  │
  ▼
Step 5: [输出]
        output/YYYY-MM-DD-主题名.md
```

---

## 七、与 live-content-studio 的对比

| 维度 | live-content-studio | ebook-content-studio |
|------|-------------------|---------------------|
| **目标** | 热点→视频自动化 | 电子书→脚本生成 |
| **大模型** | DeepSeek Flash (云端API) | **Qwen3.5 (本地)** |
| **推理引擎** | OpenClaw (sessions_spawn) | **llama.cpp (编译版)** |
| **向量库** | 无（直接 feed 上下文） | **ChromaDB (本地持久化)** |
| **数据源** | 热点平台（都音/知乎/微博） | **私有电子书库** |
| **产出** | 1080×1920 竖屏视频 | **Markdown 脚本/大纲** |
| **Agent编排** | OpenClaw 子Agent链式调用 | **Python 函数链式调用** |
| **依赖** | edge-tts + moviepy + pillow | **chromadb + PyMuPDF + sqlite3** |
| **网络依赖** | 需要访问热点平台 | **完全离线可用** |
| **隐私安全** | 热点数据公开 | **所有数据不出本地** |

---

## 八、实施路线图

### Phase 1：基础设施（1 周）
- [ ] 搭建项目目录结构
- [ ] 实现 `core/llm.py` — llama.cpp 调用封装
- [ ] 实现 `core/embedding.py` — 向量生成封装
- [ ] 验证 Qwen3.5 + llama.cpp 能正常推理

### Phase 2：电子书预处理（1-2 周）
- [ ] 实现 TXT/PDF 解析器
- [ ] 实现章节识别器（正则 + Qwen3.5）
- [ ] 实现语义分块器
- [ ] 实现 `scripts/import_book.py` 批量入库脚本

### Phase 3：检索系统（1 周）
- [ ] 搭建 ChromaDB 向量存储
- [ ] 搭建 SQLite FTS5 全文索引
- [ ] 实现混合检索引擎
- [ ] 实现 Qwen3.5 重排序模块

### Phase 4：智能生成层（2 周）
- [ ] 实现需求分析 Agent
- [ ] 实现素材规划 Agent
- [ ] 实现脚本生成 Agent（三段式生成）
- [ ] 实现 `generate.py` 主入口

### Phase 5：优化与测试（1 周）
- [ ] 生成质量评估（覆盖度/一致性/引用准确性）
- [ ] 交互模式支持
- [ ] 边缘情况处理（素材不足/长文本断裂）
- [ ] 性能优化（缓存/批量向量化）

---

## 九、已知问题与优化方向

### 9.1 本地模型 vs API 模型的差异

| 方面 | Qwen3.5 本地 | DeepSeek Flash API |
|------|-------------|-------------------|
| **响应速度** | 较慢（~10 tokens/s）| 快（~50 tokens/s）|
| **上下文窗口** | 8K tokens | 128K tokens |
| **长文本处理** | 需分段+拼接 | 可直接处理 |
| **成本** | 0（仅电费） | $0.14/1M input |
| **隐私** | ✅ 完全本地 | ❌ 数据需上传 |

### 9.2 优化方向

1. **分段生成的上下文连贯性** — 每次分段生成时携带上段摘要，保持一致性
2. **素材不足处理** — 当检索结果不足时，让 Qwen3.5 基于已有素材进行合理扩展
3. **缓存机制** — 对相同查询的检索结果做缓存，避免重复计算
4. **增量索引** — 新增电子书时只处理新增内容，不重建全量索引
5. **批量向量化** — 用 llama.cpp batch embedding 接口一次处理多个文本块
6. **多线程并行** — 分段生成时各段可并行调用 llama.cpp（需注意显存限制）

### 9.3 风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|---------|
| PDF 排版混乱 | 解析失败率高 | 提供人工校对接口 + 降级到纯文本提取 |
| 素材不足 | 生成内容空洞 | 素材缺口提示 + Qwen3.5 常识补充 |
| 长文本生成断裂 | 前后不一致 | 大纲锁定 + 段摘要传递 + 一致性检查 |
| 本地模型速度慢 | 用户体验差 | 交互模式 + 进度显示 + 后台异步生成 |
| 硬件资源不足 | 模型无法运行 | 支持更小模型 Qwen3.5-7B / Qwen2.5-7B |

---

## 十、配置文件参考

```yaml
# config/default.yaml
model:
  llm_path: "C:/models/qwen3.5-14b-Q4_K_M.gguf"
  llm_cli: "C:/tools/llama.cpp/build/bin/llama-cli.exe"
  embed_path: "C:/models/bge-m3-Q4_K_M.gguf"
  embed_cli: "C:/tools/llama.cpp/build/bin/llama-embedding.exe"
  context_size: 8192
  max_tokens: 4096
  temperature: 0.7

retrieval:
  top_k_vector: 50
  top_k_fts: 50
  top_k_rerank: 20
  rrf_k: 60
  max_context_tokens: 4096

chunking:
  target_tokens: 512
  overlap_tokens: 128
  min_tokens: 128

storage:
  vector_db: "./data/vector_db"
  sqlite: "./data/library.db"
  raw_books: "./data/raw_books"
  processed: "./data/processed"
```

---

*版本：v1.0｜2026-05-27｜基于 live-content-studio 模式，适配本地 Qwen3.5 + llama.cpp*