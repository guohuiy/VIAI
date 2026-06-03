"""
生成编排服务
编排需求分析 → 素材检索 → 脚本生成的完整流程
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from agents.generation_agent import GenerationAgent
from agents.material_agent import MaterialAgent
from agents.requirement_agent import RequirementAgent


class GenerationService:
    """生成编排服务"""

    def __init__(self):
        self.requirement_agent = RequirementAgent()
        self.material_agent = MaterialAgent()
        self.generation_agent = GenerationAgent()

    def generate(
        self,
        theme: str,
        style: str = "科普",
        word_count: int = 3000,
        audience: str = "大众",
        interactive: bool = False,
    ) -> Dict[str, Any]:
        """
        完整生成流程

        Args:
            theme: 主题
            style: 风格
            word_count: 目标字数
            audience: 受众
            interactive: 是否交互模式

        Returns:
            生成结果
        """
        # Step 1: 需求分析
        print("📋 Step 1/4: 需求分析中...")
        analysis_result = self.requirement_agent.execute({
            "theme": theme,
            "style": style,
            "word_count": word_count,
            "audience": audience,
        })

        if "error" in analysis_result:
            return {"error": analysis_result["error"]}

        print(f"   主题拆解为 {len(analysis_result.get('sub_themes', []))} 个子主题")

        # Step 2: 素材检索与规划
        print("📚 Step 2/4: 素材检索中...")
        material_result = self.material_agent.execute({
            "analysis_result": analysis_result,
        })

        coverage = material_result.get("coverage_summary", {})
        print(f"   素材覆盖度: {coverage.get('adequate', 0)}/{coverage.get('total_sub_themes', 0)}")

        if interactive:
            # 交互模式：显示大纲供用户确认
            outline = self.generation_agent._generate_outline(
                analysis_result,
                material_result.get("combined_context", ""),
            )
            print(f"\n📝 大纲预览:\n{outline}\n")
            user_input = input("是否继续生成？(y/n): ")
            if user_input.lower() != "y":
                return {"status": "cancelled", "outline": outline}

        # Step 3: 脚本生成
        print("✍️  Step 3/4: 脚本生成中...")
        generation_result = self.generation_agent.execute({
            "analysis_result": analysis_result,
            "combined_context": material_result.get("combined_context", ""),
        })

        print(f"   已生成 {generation_result.get('word_count', 0)} 字")

        # Step 4: 输出保存
        print("💾 Step 4/4: 保存输出...")
        output_path = self._save_output(theme, generation_result)

        print(f"✅ 生成完成！输出文件: {output_path}")

        return {
            "status": "success",
            "analysis": analysis_result,
            "material_coverage": coverage,
            "output_path": str(output_path),
            "word_count": generation_result.get("word_count", 0),
            "outline": generation_result.get("outline", ""),
            "full_script": generation_result.get("full_script", ""),
        }

    def generate_material_only(
        self,
        theme: str,
        style: str = "科普",
    ) -> Dict[str, Any]:
        """
        仅素材检索预览

        Args:
            theme: 主题
            style: 风格

        Returns:
            检索结果
        """
        analysis_result = self.requirement_agent.execute({
            "theme": theme,
            "style": style,
        })

        material_result = self.material_agent.execute({
            "analysis_result": analysis_result,
        })

        return {
            "analysis": analysis_result,
            "material": material_result,
        }

    def _save_output(self, theme: str, result: Dict[str, Any]) -> Path:
        """保存生成结果为 Markdown 文件"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_theme = theme.replace(" ", "_").replace("/", "_")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{date_str}-{safe_theme}.md"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {theme}\n\n")
            f.write(f"> 生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # 大纲
            f.write("## 大纲\n\n")
            f.write(result.get("outline", ""))
            f.write("\n\n---\n\n")

            # 完整脚本
            f.write("## 完整脚本\n\n")
            f.write(result.get("full_script", ""))

        return output_path
