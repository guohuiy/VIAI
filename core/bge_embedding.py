"""
BGE-M3 向量生成模块
通过 ONNX Runtime 本地运行 BGE-M3 嵌入模型
"""

import time
from pathlib import Path
from typing import List

import numpy as np

# BGE-M3 模型路径
BGE_DIR = Path(__file__).resolve().parent.parent / "models" / "bge-m3"
ONNX_PATH = BGE_DIR / "onnx" / "model.onnx"

# 最大输入长度
MAX_SEQ_LEN = 8192


class BgeM3Embedding:
    """BGE-M3 嵌入模型封装（ONNX Runtime）"""

    def __init__(self):
        self._session = None
        self._tokenizer = None

    def _load(self):
        """延迟加载模型和分词器"""
        if self._session is not None:
            return

        if not ONNX_PATH.exists():
            raise RuntimeError(
                f"BGE-M3 ONNX 模型不存在: {ONNX_PATH}\n"
                "请确认 models/bge-m3/onnx/ 目录包含 model.onnx 和 model.onnx_data"
            )

        import onnxruntime as ort

        t0 = time.time()
        self._session = ort.InferenceSession(
            str(ONNX_PATH),
            providers=['CPUExecutionProvider'],
        )
        t1 = time.time()

        # 初始化分词器（使用 transformers 或手工加载）
        self._tokenizer = self._load_tokenizer()
        t2 = time.time()
        print(f"  [BGE-M3] 模型加载 {t1-t0:.1f}s, 分词器 {t2-t1:.1f}s")

    def _load_tokenizer(self):
        """加载 BGE-M3 的分词器"""
        try:
            from transformers import AutoTokenizer
            return AutoTokenizer.from_pretrained(str(BGE_DIR), use_fast=False)
        except ImportError:
            # fallback: 使用 sentencepiece 直接加载
            from tokenizers import Tokenizer
            tok_path = BGE_DIR / "onnx" / "tokenizer.json"
            if tok_path.exists():
                return Tokenizer.from_file(str(tok_path))
            raise RuntimeError(
                "需要安装 transformers: pip install transformers\n"
                "或确认 models/bge-m3/onnx/tokenizer.json 存在"
            )

    def get_embedding(self, text: str, normalize: bool = True) -> List[float]:
        """
        生成单段文本的 embedding 向量

        Args:
            text: 输入文本
            normalize: 是否 L2 归一化

        Returns:
            1024 维浮点数向量
        """
        self._load()
        return self._encode([text], normalize=normalize)[0]

    def get_batch_embeddings(
        self,
        texts: List[str],
        normalize: bool = True,
    ) -> List[List[float]]:
        """
        批量生成 embedding 向量

        Args:
            texts: 文本列表
            normalize: 是否 L2 归一化

        Returns:
            向量列表
        """
        self._load()
        return self._encode(texts, normalize=normalize)

    def _encode(self, texts: List[str], normalize: bool = True) -> List[List[float]]:
        """
        执行编码

        Args:
            texts: 文本列表
            normalize: 是否 L2 归一化
        """
        # 1. 分词
        if hasattr(self._tokenizer, "__call__"):
            # HuggingFace tokenizer
            encoded = self._tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=MAX_SEQ_LEN,
                return_tensors="np",
            )
            input_ids = encoded["input_ids"].astype(np.int64)
            attention_mask = encoded["attention_mask"].astype(np.int64)
            token_type_ids = encoded.get(
                "token_type_ids",
                np.zeros_like(input_ids, dtype=np.int64),
            ).astype(np.int64)
        else:
            # tokenizers 库
            encoded = self._tokenizer.encode_batch(texts)
            max_len = min(
                max(len(e.ids) for e in encoded) if encoded else 0,
                MAX_SEQ_LEN,
            )
            batch_size = len(texts)
            input_ids = np.zeros((batch_size, max_len), dtype=np.int64)
            attention_mask = np.zeros((batch_size, max_len), dtype=np.int64)

            for i, e in enumerate(encoded):
                ids = e.ids[:max_len]
                input_ids[i, :len(ids)] = ids
                attention_mask[i, :len(ids)] = 1

            token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

        # 2. ONNX 推理
        input_name = self._session.get_inputs()[0].name
        outputs = self._session.run(
            None,
            {
                input_name: input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            },
        )

        # 3. 取最后一层 hidden state 做 mean pooling
        last_hidden = outputs[0]  # [batch, seq_len, dim]
        mask = attention_mask[:, :, np.newaxis].astype(np.float32)
        masked = last_hidden * mask
        summed = masked.sum(axis=1)
        count = mask.sum(axis=1).clip(min=1e-9)
        embeddings = summed / count  # [batch, dim]

        # 4. L2 归一化
        if normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.clip(norms, 1e-12, None)
            embeddings = embeddings / norms

        return embeddings.tolist()


# 全局单例
_global_bge = None


def get_bge() -> BgeM3Embedding:
    """获取 BGE-M3 全局实例"""
    global _global_bge
    if _global_bge is None:
        _global_bge = BgeM3Embedding()
    return _global_bge


def get_embedding(text: str) -> List[float]:
    """便捷接口：生成单段文本 embedding"""
    return get_bge().get_embedding(text)


def get_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """便捷接口：批量生成 embedding"""
    return get_bge().get_batch_embeddings(texts)
