"""
Agent 基类
定义所有 Agent 的公共接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Agent 任务

        Args:
            context: 输入上下文

        Returns:
            输出结果
        """
        pass