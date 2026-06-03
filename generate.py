#!/usr/bin/env python3
"""
ebook-content-studio 主入口（命令行工具）
基于私有电子书库生成指定主题/风格/字数的内容脚本

用法:
    # 一键生成
    python generate.py "人工智能发展简史" --style 科普 --words 3000

    # 交互模式（逐步骤确认）
    python generate.py "量子计算入门" --interactive

    # 仅素材检索预览
    python generate.py "深度学习" --step material --show-sources
"""

import argparse
import io
import sys
from pathlib import Path

# Windows GBK 编码兼容：设置标准输出为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).resolve().parent))

from services.generation_service import GenerationService  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="ebook-content-studio - 私有电子书内容生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "人工智能发展简史" --style 科普 --words 3000
  %(prog)s "量子计算入门" --interactive
  %(prog)s "深度学习" --step material --show-sources
        """,
    )

    parser.add_argument(
        "theme",
        type=str,
        help="生成主题（必填）",
    )
    parser.add_argument(
        "--style",
        type=str,
        default="科普",
        help="生成风格（默认: 科普）",
    )
    parser.add_argument(
        "--words",
        type=int,
        default=3000,
        help="目标字数（默认: 3000）",
    )
    parser.add_argument(
        "--audience",
        type=str,
        default="大众",
        help="目标受众（默认: 大众）",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互模式（逐步骤确认）",
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=["all", "material"],
        default="all",
        help="执行步骤（默认: all）",
    )
    parser.add_argument(
        "--show-sources",
        action="store_true",
        help="显示素材来源",
    )

    args = parser.parse_args()
    service = GenerationService()

    if args.step == "material":
        # 仅素材检索预览
        print(f"\n🔍 素材检索预览: {args.theme}\n")
        result = service.generate_material_only(
            theme=args.theme,
            style=args.style,
        )

        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)

        material = result.get("material", {})
        coverage = material.get("coverage_summary", {})
        print(f"📊 素材覆盖度: {coverage.get('adequate', 0)}/{coverage.get('total_sub_themes', 0)}")

        if args.show_sources:
            context = material.get("combined_context", "")
            if context:
                print(f"\n📄 素材来源:\n{context[:2000]}...")

        return

    # 完整生成流程
    print(f"\n🚀 开始生成: {args.theme}\n")
    print(f"   风格: {args.style}")
    print(f"   目标字数: {args.words}")
    print(f"   受众: {args.audience}\n")

    result = service.generate(
        theme=args.theme,
        style=args.style,
        word_count=args.words,
        audience=args.audience,
        interactive=args.interactive,
    )

    if "error" in result:
        print(f"❌ {result['error']}")
        sys.exit(1)

    if result.get("status") == "cancelled":
        print("⏹  用户取消生成")
        sys.exit(0)

    print("\n✅ 生成完成!")
    print(f"📄 输出文件: {result.get('output_path', 'N/A')}")
    print(f"📝 实际字数: {result.get('word_count', 0)}")


if __name__ == "__main__":
    main()
