# 📚 ebook-content-studio — 私有电子书内容生成系统

> 基于 Qwen3.5 + llama.cpp 的全本地化、隐私安全的智能内容生成平台

[![CI/CD](https://github.com/guohuiy/virtual-ai-presenter/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/guohuiy/virtual-ai-presenter/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20|%203.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 系统架构

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

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载模型文件

将以下 GGUF 模型文件放入 `models/` 目录：
- `qwen3.5-14b-Q4_K_M.gguf` — Qwen3.5 量化模型
- `bge-m3-Q4_K_M.gguf` — 嵌入模型

### 3. 配置模型路径

编辑 `config/default.yaml`，将模型路径指向你的实际文件位置。

### 4. 导入电子书

电子书支持两种来源：

#### 方式1：放入 data/raw_books/
将 `.txt/.pdf` 文件放入 `data/raw_books/` 目录：
```
data/raw_books/
└── 我的书.txt
```

#### 方式2：从分类目录扫描（推荐）
如果书籍按分类整理在目录中（如 `C:/books/历史军事/xxx.txt`），可以直接扫描全部分类：
```
C:/books/（你的书籍根目录）
├── 历史军事/
├── 幽默笑话/
├── 哲学理论/
├── ... （23+ 个分类）
```

**支持的命令：**

| 命令 | 说明 |
|------|------|
| `python scripts/import_book.py` | 扫描 `data/raw_books/` 下的 `.txt/.pdf` |
| `python scripts/import_book.py --full-scan` | 全量扫描 `C:/books/` 分类目录（推荐） |
| `python scripts/import_book.py --full-scan --category "历史军事"` | 只导入指定分类 |
| `python scripts/import_book.py --dir <路径>` | 从指定目录扫描 |
| `python scripts/import_book.py --dir "C:/books/幽默笑话"` | 导入单个分类目录 |
| `python scripts/import_book.py 文件1.txt 文件2.pdf` | 导入指定文件 |
| `python scripts/import_book.py --list` | 列出已导入的书籍（含分类统计） |
| `python scripts/import_book.py --reindex` | 重新导入（覆盖旧数据） |
| `python scripts/import_book.py --skip-existing` | 跳过已存在的文件（MD5去重） |
| `python scripts/import_book.py --dry-run` | 预览模式（只看不导入） |

**导入特征：**
- 自动保留分类标签（category），检索时可按分类过滤
- 自动检测文件编码（修复 chardet 对中文编码的误判）
- 自动检测语言类型（中文/中英混合/英文）
- 自动提取书籍摘要
- MD5 文件去重，同一文件不重复导入
- 批量事务写入，高性能入库

**导入后重建向量索引（导入时用零向量占位以加速）：**
```bash
python scripts/build_index.py
```

### 5. 生成内容

```bash
# 一键生成
python generate.py "人工智能发展简史" --style 科普 --words 3000

# 交互模式
python generate.py "量子计算入门" --interactive

# 仅素材检索预览
python generate.py "深度学习" --step material --show-sources
```

## 项目结构

```
ebook-content-studio/
├── core/                  # 核心引擎（LLM调用、向量生成、配置）
├── preprocessing/         # 预处理层（文档解析、章节识别、语义分块）
├── retrieval/             # 检索层（向量检索、全文检索、混合检索）
├── agents/                # 智能层（需求分析、素材规划、脚本生成 Agent）
├── services/              # 业务服务（书籍入库、生成编排）
├── storage/               # 数据层（SQLite、向量数据库操作）
├── scripts/               # 工具脚本（导入、重建索引）
├── data/                  # 数据目录
├── models/                # 模型文件
├── runtime/               # 运行时状态
├── output/                # 生成结果
├── config/                # 配置文件
├── generate.py            # 主入口
└── requirements.txt       # Python 依赖
```

## 持续集成

本项目使用 **GitHub Actions** 进行自动化 CI/CD，每次 Push 和 Pull Request 自动触发。

### CI 管道

| 阶段 | Job | 检查内容 |
|------|-----|----------|
| 🔍 **代码质量** | `lint` | flake8 语法检查 + ruff 代码风格 |
| 🧪 **单元测试** | `test` | pytest 运行测试 + 覆盖率报告 |
| 📦 **构建验证** | `build-check` | 模块导入验证 + wheel 打包 |
| 🔒 **安全扫描** | `security` | safety 依赖漏洞扫描 |
| 🚀 **发布** | `release` | 打 `v*` tag 时自动发布到 PyPI |

### 测试

```bash
# 安装测试依赖
pip install -r requirements.txt pytest pytest-cov

# 运行测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=./ --cov-report=term-missing
```

### CI 徽章状态

[![CI/CD](https://github.com/guohuiy/virtual-ai-presenter/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/guohuiy/virtual-ai-presenter/actions/workflows/ci.yml)

对应文件：`.github/workflows/ci.yml`、`pyproject.toml`、`.gitignore`、`requirements.txt`

## 技术栈

| 组件 | 选型 |
|------|------|
| 大模型 | Qwen3.5-14B (GGUF) |
| 推理引擎 | llama.cpp |
| 嵌入模型 | BGE-M3 |
| 向量数据库 | ChromaDB |
| 结构化存储 | SQLite |
| 全文检索 | SQLite FTS5 |
| 文档解析 | PyMuPDF + chardet |
| CI/CD | GitHub Actions |
| 打包 | setuptools + build |
| 测试 | pytest + coverage |
| 代码检查 | flake8 + ruff + safety |
