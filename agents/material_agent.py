"""
素材规划 Agent
为每个子主题生成检索查询，调用混合检索获取素材，评估覆盖度
"""

from typing import Any, Dict, List

from retrieval.context_assembler import ContextAssembler
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker

from .base import BaseAgent


class MaterialAgent(BaseAgent):
    """素材规划 Agent"""

    def __init__(self):
        super().__init__(name="material_agent")
        self.retriever = HybridRetriever()
        self.reranker = Reranker()
        self.context_assembler = ContextAssembler()

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行素材规划

        context 期望参数:
            - analysis_result: 需求分析结果（含 sub_themes, material_queries）

        Returns:
            - material_plan: 各子主题的素材计划
            - combined_context: 组装后的上下文
            - coverage_summary: 素材覆盖度总结
        """
        analysis = context.get("analysis_result", {})
        sub_themes = analysis.get("sub_themes", [])
        material_queries = analysis.get("material_queries", [])

        if not sub_themes:
            return {"error": "缺少子主题列表"}

        material_plan = []
        all_retrieved = []

        for sub_theme in sub_themes:
            # 查找该子主题的查询词
            queries = self._get_queries_for_topic(sub_theme, material_queries)

            # 混合检索
            sub_results = self._search_for_topic(sub_theme, queries)
            all_retrieved.extend(sub_results)

            # 评估覆盖度
            coverage = "adequate" if len(sub_results) >= 3 else "insufficient"
            gaps = [] if coverage == "adequate" else [f"子主题「{sub_theme}」素材不足，需要补充"]

            material_plan.append({
                "sub_theme": sub_theme,
                "queries": queries,
                "retrieved_chunks": [c["id"] for c in sub_results[:5]],
                "coverage": coverage,
                "gaps": gaps,
            })

        # 对所有结果进行重排序
        if all_retrieved:
            combined_query = analysis.get("core_theme", "")
            all_retrieved = self.reranker.rerank(combined_query, all_retrieved)

        # 组装上下文
        combined_context = self.context_assembler.assemble(all_retrieved)

        # 统计覆盖度
        total = len(material_plan)
        adequate = sum(1 for m in material_plan if m["coverage"] == "adequate")
        coverage_summary = {
            "total_sub_themes": total,
            "adequate": adequate,
            "insufficient": total - adequate,
            "overall": "adequate" if adequate >= total * 0.6 else "insufficient",
        }

        return {
            "material_plan": material_plan,
            "combined_context": combined_context,
            "coverage_summary": coverage_summary,
        }

    def _get_queries_for_topic(
        self,
        topic: str,
        material_queries: List[Dict[str, Any]],
    ) -> List[str]:
        """获取指定主题的查询词"""
        for mq in material_queries:
            if mq.get("topic") == topic:
                return mq.get("queries", [topic])
        # 默认查询
        return [
            topic,
            f"{topic} 定义 概念",
            f"{topic} 案例 例子",
        ]

    def _search_for_topic(
        self,
        topic: str,
        queries: List[str],
    ) -> List[Dict[str, Any]]:
        """对某个主题执行多查询检索"""
        all_results = []
        seen_ids = set()

        for q in queries:
            results = self.retriever.search(q, top_k=10)
            for r in results:
                if r["id"] not in seen_ids:
                    all_results.append(r)
                    seen_ids.add(r["id"])

        return all_results
