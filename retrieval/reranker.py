"""
重排序模块
使用 Qwen3.5 对候选结果进行相关性判断和重排序
"""

from typing import Any, Dict, List

from core.llm import call_llama_cpp, parse_json_from_response


class Reranker:
    """Qwen3.5 重排序器"""

    def __init__(self):
        self._cache: Dict[str, List[str]] = {}

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        使用 LLM 对候选结果进行重排序

        Args:
            query: 原查询
            candidates: 候选结果列表

        Returns:
            重排序后的结果列表
        """
        if len(candidates) <= 1:
            return candidates

        # 构建 prompt
        candidates_text = "\n".join(
            f"[{i}] {c['content'][:200]}"
            for i, c in enumerate(candidates)
        )

        prompt = f"""判断以下素材与查询的相关性，从高到低排序。

查询：{query}

素材列表：
{candidates_text}

请输出排序后的序号列表（最相关在前），格式：[3, 0, 1, 2]
注意：只需输出 JSON 格式的序号列表，不要输出其他内容。
"""
        try:
            response = call_llama_cpp(prompt, max_tokens=200, temperature=0.1)
            indices = self._parse_indices(response)

            if not indices:
                return candidates

            # 按 LLM 排序结果重新排列
            reranked = []
            seen = set()
            for idx in indices:
                if idx not in seen and idx < len(candidates):
                    reranked.append(candidates[idx])
                    seen.add(idx)

            # 补充未出现的候选
            for i in range(len(candidates)):
                if i not in seen:
                    reranked.append(candidates[i])

            return reranked

        except Exception:
            # fallback: 返回原始顺序
            return candidates

    def _parse_indices(self, response: str) -> List[int]:
        """解析 LLM 返回的序号列表"""
        import re

        # 尝试匹配 JSON 数组
        try:
            parsed = parse_json_from_response(response)
            if isinstance(parsed, list):
                return [int(i) for i in parsed]
        except (ValueError, KeyError):
            pass

        # 尝试匹配 [num, num, num] 模式
        match = re.search(r'\[([\d,\s]+)\]', response)
        if match:
            return [
                int(i.strip())
                for i in match.group(1).split(",")
                if i.strip().isdigit()
            ]

        return []
