"""
ChromaDB 向量存储操作模块
封装向量数据库的增删查等操作
"""

from typing import Any, Dict, List, Optional

from core.config import STORAGE_CONFIG


class VectorStore:
    """ChromaDB 向量存储操作类"""

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or STORAGE_CONFIG["vector_db"]
        self._client = None
        self._collection = None

    @property
    def client(self):
        """获取 ChromaDB 客户端（懒加载）"""
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=self.persist_dir)
        return self._client

    @property
    def collection(self):
        """获取默认集合（懒加载）"""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name="book_chunks",
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_chunks(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        添加分块到向量数据库

        Args:
            ids: 分块 ID 列表
            embeddings: 向量列表
            documents: 文本内容列表
            metadatas: 元数据列表
        """
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 50,
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        向量检索

        Args:
            query_embedding: 查询向量
            top_k: 返回顶部 K 个结果
            filter_criteria: 过滤条件

        Returns:
            检索结果列表
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_criteria,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        return [
            {
                "id": ids[i],
                "content": documents[i],
                "metadata": metadatas[i],
                "score": 1 - distances[i],  # 距离转相似度
                "source": "vector",
            }
            for i in range(len(ids))
        ]

    def delete_chunks(self, ids: List[str]) -> None:
        """删除指定分块"""
        self.collection.delete(ids=ids)

    def count(self) -> int:
        """获取集合中的文档数量"""
        return self.collection.count()

    def get_collection_names(self) -> List[str]:
        """获取所有集合名称"""
        return self.client.list_collections()
