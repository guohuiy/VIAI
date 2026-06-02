"""
需求分析 Agent
分析用户输入的主题/风格/字数需求，拆解为子主题和素材查询
"""

import json
from typing import Dict, Any, List

from .base import BaseAgent
from core.llm import call_llama_cpp, parse_json_from_response


class RequirementAgent(BaseAgent):
    """需求分析 Agent"""

    def __init__(self):
        super().__init__(name="requirement_agent")

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行需求分析

        context 期望参数:
            - theme: 主题
            - style: 风格（可选，默认"科普"）
            - word_count: 目标字数（可选，默认3000）
            - audience: 受众（可选，默认"大众"）

        Returns:
            - core_theme: 核心主题
            - sub_themes: 子主题列表
            - style_profile: 风格特征
            - material_queries: 素材查询列表
            - estimated_sections: 预计章节数
            - target_word_count: 目标字数
        """
        theme = context.get("theme", "")
        style = context.get("style", "科普")
        word_count = context.get("word_count", 3000)
        audience = context.get("audience", "大众")

        if not theme:
            return {"error": "缺少主题参数"}

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
  "target_word_count": {word_count}
}}
```
"""
        response = call_llama_cpp(prompt, max_tokens=1024)

        try:
            result = parse_json_from_response(response)
            # 确保必要字段存在
            result.setdefault("core_theme", theme)
            result.setdefault("sub_themes", [theme])
            result.setdefault("style_profile", {"tone": style, "language": "中文", "narrative": "叙事"})
            result.setdefault("material_queries", [])
            result.setdefault("estimated_sections", 5)
            result.setdefault("target_word_count", word_count)
            return result
        except (ValueError, json.JSONDecodeError) as e:
            # fallback: 返回基本结构
            return {
                "core_theme": theme,
                "sub_themes": [theme],
                "style_profile": {
                    "tone": style,
                    "language": "中文",
                    "narrative": "科普叙事",
                },
                "material_queries": [
                    {"topic": theme, "queries": [theme, f"{theme} 概念", f"{theme} 案例"]}
                ],
                "estimated_sections": 3,
                "target_word_count": word_count,
                "_parse_error": str(e),
            }