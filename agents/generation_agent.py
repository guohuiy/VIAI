"""
脚本生成 Agent
三段式生成策略：大纲 → 分段生成 → 后处理
"""

from typing import Any, Dict, List

from core.llm import call_llama_cpp

from .base import BaseAgent


class GenerationAgent(BaseAgent):
    """脚本生成 Agent"""

    def __init__(self):
        super().__init__(name="generation_agent")

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行脚本生成

        context 期望参数:
            - analysis_result: 需求分析结果
            - combined_context: 检索组装的上下文

        Returns:
            - outline: 生成的脚本大纲
            - sections: 各段内容
            - full_script: 完整脚本
            - word_count: 实际字数
        """
        analysis = context.get("analysis_result", {})
        material_context = context.get("combined_context", "")

        # A. 大纲生成
        outline = self._generate_outline(analysis, material_context)

        # B. 分段生成
        sections = self._generate_sections(outline, analysis, material_context)

        # C. 后处理
        full_script = "\n\n".join(sections)
        target_word_count = analysis.get("target_word_count", 3000)
        full_script = self._post_process(full_script, target_word_count)

        # 统计字数
        actual_count = len(full_script.replace(" ", "").replace("\n", ""))

        return {
            "outline": outline,
            "sections": sections,
            "full_script": full_script,
            "word_count": actual_count,
        }

    def _generate_outline(self, analysis: Dict[str, Any], material: str) -> str:
        """生成脚本大纲"""
        theme = analysis.get("core_theme", "")
        style = analysis.get("style_profile", {})
        tone = style.get("tone", "科普")
        target_count = analysis.get("target_word_count", 3000)
        estimated_sections = analysis.get("estimated_sections", 5)

        prompt = f"""基于以下素材和需求，生成一个{tone}风格的脚本大纲。

## 主题
{theme}

## 素材内容
{material}

## 要求
- 总字数约{target_count}字
- 包含{estimated_sections}个主要部分
- 每部分标注核心素材来源

请输出 Markdown 格式的脚本大纲。
"""
        return call_llama_cpp(prompt, max_tokens=2048)

    def _generate_sections(
        self,
        outline: str,
        analysis: Dict[str, Any],
        material: str,
    ) -> List[str]:
        """分段生成脚本内容"""
        style = analysis.get("style_profile", {})
        tone = style.get("tone", "科普")
        language = style.get("language", "中文")
        narrative = style.get("narrative", "叙事")

        # 从大纲中提取各部分标题
        section_titles = self._parse_section_titles(outline)
        if not section_titles:
            section_titles = ["引言", "主体内容", "总结"]

        sections = []
        word_count_per_section = max(
            analysis.get("target_word_count", 3000) // len(section_titles),
            500,
        )

        for i, title in enumerate(section_titles):
            prompt = f"""请基于以下素材，生成脚本的第{i+1}部分「{title}」。

## 风格要求
- 语调：{tone}
- 语言：{language}
- 叙事方式：{narrative}

## 字数要求
约{word_count_per_section}字

## 素材内容
{material}

## 注意事项
1. 自然融入素材，不要生硬堆砌
2. 保持叙事连贯性
3. 引用原文观点时标注来源
"""
            section = call_llama_cpp(prompt, max_tokens=4096)
            sections.append(section)

        return sections

    def _post_process(self, full_script: str, target_word_count: int) -> str:
        """后处理：字数校准、风格统一、引用规范化"""
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

    def _parse_section_titles(self, outline: str) -> List[str]:
        """从大纲中解析各部分标题"""
        import re
        titles = []
        for line in outline.split("\n"):
            line = line.strip()
            # 匹配 Markdown 标题
            if re.match(r"^#{1,3}\s+", line):
                title = re.sub(r"^#+\s*", "", line)
                if title:
                    titles.append(title)
        return titles
