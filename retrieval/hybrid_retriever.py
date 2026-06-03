"""
混合检索引擎
融合向量检索 + 全文检索结果，使用 RRF 算法
"""

from typing import Any, Dict, List, Optional

from core.config import RETRIEVAL_CONFIG
from core.embedding import get_embedding

from .fulltext_engine import FullTextEngine
from .vector_store import VectorStore


class HybridRetriever:
    """混合检索引擎"""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        fulltext_engine: Optional[FullTextEngine] = None,
    ):
        self.vector_store = vector_store or VectorStore()
        self.fulltext_engine = fulltext_engine or FullTextEngine()
        self.top_k_vector = RETRIEVAL_CONFIG["top_k_vector"]
        self.top_k_fts = RETRIEVAL_CONFIG["top_k_fts"]
        self.rrf_k = RETRIEVAL_CONFIG["rrf_k"]

    def search(
        self,
        query: str,
        top_k: int = 20,
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        混合检索：向量 + 全文检索 + RRF 融合

        Args:
            query: 查询文本
            top_k: 最终返回结果数
            filter_criteria: 过滤条件

        Returns:
            融合排序后的结果列表
        """
        # 1. 向量检索
        query_embedding = get_embedding(query)
        vector_results = self.vector_store.search(
            query_embedding,
            top_k=self.top_k_vector,
            filter_criteria=filter_criteria,
        )

        # 2. 全文检索
        fts_results = self.fulltext_engine.search(
            query,
            top_k=self.top_k_fts,
        )

        # 3. RRF 融合
        fused = self._rrf_fusion(vector_results, fts_results)

        return fused[:top_k]

    def _rrf_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        fts_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion 融合算法

        Args:
            vector_results: 向量检索结果
            fts_results: 全文检索结果

        Returns:
            融合后按分数降序排列的结果
        """
        scores = {}

        for rank, doc in enumerate(vector_results):
            doc_id = doc["id"]
            score = 1.0 / (self.rrf_k + rank + 1)
            if doc_id in scores:
                scores[doc_id]["score"] += score
            else:
                scores[doc_id] = dict(doc)
                scores[doc_id]["score"] = score
                scores[doc_id]["source"] = "hybrid"

        for rank, doc in enumerate(fts_results):
            doc_id = doc["id"]
            score = 1.0 / (self.rrf_k + rank + 1)
            if doc_id in scores:
                scores[doc_id]["score"] += score
            else:
                scores[doc_id] = dict(doc)
                scores[doc_id]["score"] = score
                scores[doc_id]["source"] = "hybrid"

        # 按分数降序排列
        return sorted(
            scores.values(),
            key=lambda x: -x["score"],
        )
