"""
解析器基类
定义所有文档解析器的公共接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TextBlock:
    """文本块元数据"""
    text: str
    font_size: Optional[float] = None
    font_name: Optional[str] = None
    is_bold: bool = False
    bbox: Optional[tuple] = None  # (x0, y0, x1, y1)
    page_num: int = 0


@dataclass
class PageData:
    """单页解析数据"""
    text: str
    blocks: List[TextBlock] = field(default_factory=list)
    page_num: int = 0


@dataclass
class ParseResult:
    """文档解析结果"""
    pages: List[PageData] = field(default_factory=list)
    encoding: str = "utf-8"
    total_chars: int = 0
    file_path: str = ""
    file_type: str = ""


class BaseParser(ABC):
    """文档解析器基类"""

    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        """
        解析文档文件

        Args:
            file_path: 文件路径

        Returns:
            解析结果
        """
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """
        判断是否支持该文件类型

        Args:
            file_path: 文件路径

        Returns:
            是否支持
        """
        pass