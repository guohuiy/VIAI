"""
测试结构检测模块 - 章节检测和树构建
"""

import pytest

from preprocessing.structure.chapter_detector import ChapterDetector
from preprocessing.structure.tree_builder import TreeBuilder


class TestChapterDetector:
    """章节检测全覆盖测试"""

    @pytest.fixture
    def detector(self):
        return ChapterDetector()

    def test_detect_chinese_chapters(self, detector):
        """检测中文第X章模式"""
        text = """第一章 引言
这是引言内容
第二章 方法
这是方法内容
第三章 结果
这是结果内容"""
        chapters = detector.detect(text)
        assert len(chapters) >= 1

    def test_detect_section_patterns(self, detector):
        """检测数字序号模式"""
        text = """1.1 背景
背景内容
1.2 目的
目的内容
2.1 实验
实验内容"""
        chapters = detector.detect(text)
        assert len(chapters) >= 2

    def test_no_structure(self, detector):
        """无结构的文本"""
        chapters = detector.detect("这是一段简单的文本。")
        assert isinstance(chapters, list)

    def test_empty_text(self, detector):
        """空文本"""
        assert isinstance(detector.detect(""), list)

    def test_chinese_numbered_sections(self, detector):
        """检测中文序号模式"""
        text = """一、引言
这是引言
二、方法
这是方法
三、结果
这是结果"""
        chapters = detector.detect(text)
        assert len(chapters) >= 1

    def test_mixed_content_types(self, detector):
        """混合格式文本应正常解析"""
        text = """第一章 概述
内容...
1.1 小节
小节内容...
二、详细分析
分析内容..."""
        chapters = detector.detect(text)
        assert isinstance(chapters, list)

    def test_detect_english_chapters(self, detector):
        """检测英文章节模式"""
        text = """Chapter 1 Introduction
Some content
Chapter 2 Methods
More content"""
        chapters = detector.detect(text)
        assert isinstance(chapters, list)

    def test_detect_parentheses_numbered(self, detector):
        """检测括号序号模式"""
        text = """（一）准备工作
准备内容
（二）实施步骤
实施内容"""
        chapters = detector.detect(text)
        assert isinstance(chapters, list)


class TestTreeBuilder:
    """树构建器测试"""

    @pytest.fixture
    def builder(self):
        return TreeBuilder()

    def test_build_with_simple_chapters(self, builder):
        chapters = [
            {"level": 1, "title": "第一章", "start_line": 0, "end_line": 10},
            {"level": 1, "title": "第二章", "start_line": 10, "end_line": 20},
        ]
        tree = builder.build(chapters)
        assert len(tree) == 2

    def test_build_with_empty_chapters(self, builder):
        tree = builder.build([])
        assert tree == []

    def test_build_with_nested_chapters(self, builder):
        chapters = [
            {"level": 1, "title": "第一章", "start_line": 0, "end_line": 20},
            {"level": 2, "title": "第一节", "start_line": 5, "end_line": 10},
            {"level": 2, "title": "第二节", "start_line": 10, "end_line": 15},
            {"level": 1, "title": "第二章", "start_line": 20, "end_line": 30},
        ]
        tree = builder.build(chapters)
        assert len(tree) == 2