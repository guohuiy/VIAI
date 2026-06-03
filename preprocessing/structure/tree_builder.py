"""
结构树构建模块
基于识别的章节结构构建层级树
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChapterNode:
    """章节树节点"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    level: int = 1
    title: str = ""
    start_char: int = 0
    end_char: int = 0
    children: List["ChapterNode"] = field(default_factory=list)
    parent: Optional["ChapterNode"] = None


class ChapterTreeBuilder:
    """章节树构建器"""

    def build(self, chapters: List[Dict[str, Any]]) -> ChapterNode:
        """
        构建章节层级树

        Args:
            chapters: 章节列表 [{"level": 1, "title": "...", ...}]

        Returns:
            根节点（虚拟根，level=-1）
        """
        root = ChapterNode(
            id=str(uuid.uuid4()),
            level=-1,
            title="root",
        )

        if not chapters:
            return root

        # 按层级构建树
        parent_stack: List[ChapterNode] = [root]

        for ch_data in chapters:
            node = ChapterNode(
                level=ch_data.get("level", 1),
                title=ch_data.get("title", ""),
                start_char=ch_data.get("start_char", 0),
                end_char=ch_data.get("end_char", 0),
            )

            # 找到合适的父节点
            while parent_stack and parent_stack[-1].level >= node.level:
                parent_stack.pop()

            # 添加到父节点
            parent = parent_stack[-1] if parent_stack else root
            node.parent = parent
            parent.children.append(node)

            # 当前节点入栈
            parent_stack.append(node)

        return root

    def to_dict(self, node: ChapterNode) -> Dict:
        """将树节点转换为字典"""
        return {
            "id": node.id,
            "level": node.level,
            "title": node.title,
            "start_char": node.start_char,
            "end_char": node.end_char,
            "children": [self.to_dict(c) for c in node.children],
        }

    def get_all_nodes(self, node: ChapterNode) -> List[ChapterNode]:
        """获取所有节点（深度优先）"""
        nodes = [node]
        for child in node.children:
            nodes.extend(self.get_all_nodes(child))
        return nodes

    def get_leaf_nodes(self, node: ChapterNode) -> List[ChapterNode]:
        """获取所有叶子节点"""
        if not node.children:
            return [node]
        leaves = []
        for child in node.children:
            leaves.extend(self.get_leaf_nodes(child))
        return leaves
