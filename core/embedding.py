"""
向量生成接口模块
使用 sentence-transformers + BGE-M3 生成文本向量（GPU 加速）

用法：
  from core.embedding import get_embedding, get_batch_embeddings
  vec = get_embedding("你的文本")
  vecs = get_batch_embeddings(["文本1", "文本2"])
"""

import os
from typing import List
from pathlib import Path

# BGE-M3 模型路径
BGE_M3_DIR = Path(__file__).resolve().parent.parent / "models" / "bge-m3"

# 全局单例
_embedding_model = None


def _get_model():
    """懒加载 BGE-M3 模型（全局单例，GPU 加速）"""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        model_path = str(BGE_M3_DIR)
        if not os.path.exists(model_path):
            raise RuntimeError(f"BGE-M3 模型目录不存在: {model_path}")

        # 检测 GPU 是否可用
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            print(f"  [embedding] 使用 GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            print(f"  [embedding] 使用 CPU")

        _embedding_model = SentenceTransformer(model_path, device=device)

    return _embedding_model


def get_embedding(text: str) -> List[float]:
    """
    使用 BGE-M3 生成文本向量

    Args:
        text: 输入文本

    Returns:
        浮点数向量列表（1024 维）
    """
    if not text or not text.strip():
        return [0.0] * 1024

    try:
        model = _get_model()
        embedding = model.encode(text[:512], normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        raise RuntimeError(f"向量生成失败: {str(e)}")


def get_batch_embeddings(texts: List[str], batch_size: int = 256) -> List[List[float]]:
    """
    批量生成文本向量（GPU 优化：batch_size 可设大）

    Args:
        texts: 文本列表
        batch_size: 每批大小（GPU 建议 256-512，CPU 建议 32-64）

    Returns:
        向量列表
    """
    if not texts:
        return []

    try:
        model = _get_model()
        truncated = [t[:512] for t in texts]
        embeddings = model.encode(
            truncated,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return [emb.tolist() for emb in embeddings]
    except Exception as e:
        raise RuntimeError(f"批量向量生成失败: {str(e)}")