"""
全局配置模块
管理模型路径、检索参数、分块参数等所有系统配置
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ========== 模型配置 ==========
# 模型文件路径（相对于项目根目录或绝对路径）
MODEL_DIR = PROJECT_ROOT / "models" / "Qwen3.5-2B-Model"
LLAMA_CPP_DIR = Path("C:/tools/llama.cpp/build/bin/Release")

MODEL_CONFIG = {
    "llm_path": str(MODEL_DIR / "Qwen3.5-2B-Q8_0.gguf"),
    "llm_cli": str(LLAMA_CPP_DIR / "llama-cli.exe"),
    # Qwen3.5-2B 也可用于 embedding（llama.cpp 支持同模型做嵌入）
    "embed_path": str(MODEL_DIR / "Qwen3.5-2B-Q8_0.gguf"),
    "embed_cli": str(LLAMA_CPP_DIR / "llama-embedding.exe"),
    "context_size": 8192,
    "max_tokens": 4096,
    "temperature": 0.7,
}

# ========== 检索配置 ==========
RETRIEVAL_CONFIG = {
    "top_k_vector": 50,
    "top_k_fts": 50,
    "top_k_rerank": 20,
    "rrf_k": 60,
    "max_context_tokens": 4096,
}

# ========== 分块配置 ==========
CHUNKING_CONFIG = {
    "target_tokens": 512,
    "overlap_tokens": 128,
    "min_tokens": 128,
}

# ========== 存储路径配置 ==========
STORAGE_CONFIG = {
    "vector_db": str(PROJECT_ROOT / "data" / "vector_db"),
    "sqlite": str(PROJECT_ROOT / "data" / "library.db"),
    "raw_books": str(PROJECT_ROOT / "data" / "raw_books"),
    "processed": str(PROJECT_ROOT / "data" / "processed"),
}

# ========== 运行时配置 ==========
RUNTIME_CONFIG = {
    "workflow_state": str(PROJECT_ROOT / "runtime" / "workflow-state.yaml"),
}


def get_config():
    """获取合并后的完整配置"""
    return {
        "model": MODEL_CONFIG,
        "retrieval": RETRIEVAL_CONFIG,
        "chunking": CHUNKING_CONFIG,
        "storage": STORAGE_CONFIG,
        "runtime": RUNTIME_CONFIG,
    }