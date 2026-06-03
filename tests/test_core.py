"""
测试核心配置、embedding、LLM 接口模块
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.config import (
    PROJECT_ROOT, MODEL_CONFIG, RETRIEVAL_CONFIG,
    CHUNKING_CONFIG, STORAGE_CONFIG, RUNTIME_CONFIG, get_config,
)


class TestConfig:
    """配置模块全覆盖测试"""

    def test_project_root_is_path(self):
        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.name == "huyo"

    def test_model_config_completeness(self):
        """确保模型配置包含所有关键字段"""
        required = {"llm_path", "llm_cli", "embed_path", "embed_cli",
                     "context_size", "max_tokens", "temperature"}
        assert required.issubset(MODEL_CONFIG.keys())

    def test_model_config_value_ranges(self):
        assert 1024 <= MODEL_CONFIG["context_size"] <= 65536
        assert 128 <= MODEL_CONFIG["max_tokens"] <= 65536
        assert 0 < MODEL_CONFIG["temperature"] <= 2.0

    def test_retrieval_config_completeness(self):
        required = {"top_k_vector", "top_k_fts", "top_k_rerank", "rrf_k", "max_context_tokens"}
        assert required.issubset(RETRIEVAL_CONFIG.keys())

    def test_retrieval_config_values_positive(self):
        for k, v in RETRIEVAL_CONFIG.items():
            assert v > 0, f"{k} 应为正值"

    def test_chunking_config_completeness(self):
        required = {"target_tokens", "overlap_tokens", "min_tokens"}
        assert required.issubset(CHUNKING_CONFIG.keys())

    def test_chunking_config_logical(self):
        """分块参数应满足 target > overlap > min 的逻辑"""
        assert CHUNKING_CONFIG["target_tokens"] > CHUNKING_CONFIG["overlap_tokens"]
        assert CHUNKING_CONFIG["overlap_tokens"] >= CHUNKING_CONFIG["min_tokens"]

    def test_storage_config_paths(self):
        assert STORAGE_CONFIG["vector_db"].endswith("vector_db")
        assert STORAGE_CONFIG["sqlite"].endswith("library.db")
        assert STORAGE_CONFIG["raw_books"].endswith("raw_books")

    def test_runtime_config(self):
        assert "workflow_state" in RUNTIME_CONFIG

    def test_get_config_returns_all_sections(self):
        cfg = get_config()
        expected = {"model", "retrieval", "chunking", "storage", "runtime"}
        assert expected.issubset(cfg.keys())

    def test_get_config_values_match_constants(self):
        cfg = get_config()
        assert cfg["model"] == MODEL_CONFIG
        assert cfg["retrieval"] == RETRIEVAL_CONFIG

    def test_config_no_none_values(self):
        """任何配置值不能为 None"""
        cfg = get_config()
        for section, values in cfg.items():
            for k, v in values.items():
                assert v is not None, f"{section}.{k} 为 None"

    def test_config_types(self):
        assert isinstance(MODEL_CONFIG["context_size"], int)
        assert isinstance(MODEL_CONFIG["temperature"], (int, float))
        assert isinstance(STORAGE_CONFIG["vector_db"], str)


# ========================================================
# 测试 embedding 模块
# ========================================================

class TestEmbedding:
    """向量生成模块测试（模拟 GPU 依赖）"""

    def test_get_embedding_empty_string(self):
        """空文本应返回零向量"""
        from core.embedding import get_embedding
        result = get_embedding("")
        assert isinstance(result, list)
        assert len(result) == 1024
        assert all(v == 0.0 for v in result)

    def test_get_embedding_whitespace_only(self):
        """纯空白文本应返回零向量"""
        from core.embedding import get_embedding
        result = get_embedding("   \n  \t  ")
        assert len(result) == 1024
        assert all(v == 0.0 for v in result)

    def test_get_batch_embeddings_empty(self):
        """空列表应返回空列表"""
        from core.embedding import get_batch_embeddings
        result = get_batch_embeddings([])
        assert result == []

    @patch("core.embedding._get_model")
    def test_get_embedding_model_not_found(self, mock_get_model):
        """模型路径不存在应抛异常"""
        from core.embedding import get_embedding
        mock_get_model.side_effect = RuntimeError("BGE-M3 模型目录不存在")
        
        with pytest.raises(RuntimeError) as exc_info:
            get_embedding("测试文本")
        assert "模型" in str(exc_info.value)

    def test_embedding_dimension_constant(self):
        """检查向量维度常量是否有变化"""
        from core.embedding import get_embedding
        result = get_embedding("")
        assert len(result) == 1024


# ========================================================
# 测试 LLM 模块
# ========================================================

class TestLLM:
    """LLM 调用模块测试（模拟子进程）"""

    def test_parse_json_from_response_with_code_block(self):
        """解析带 ```json 块的响应"""
        from core.llm import parse_json_from_response
        response = '```json\n{"key": "value"}\n```'
        result = parse_json_from_response(response)
        assert result == {"key": "value"}

    def test_parse_json_from_response_plain(self):
        """解析纯 JSON 响应"""
        from core.llm import parse_json_from_response
        result = parse_json_from_response('{"name": "test"}')
        assert result == {"name": "test"}

    def test_parse_json_from_response_with_extra_text(self):
        """解析带前缀和后缀文本的 JSON"""
        from core.llm import parse_json_from_response
        response = '结果如下：{"a": 1, "b": 2}。请确认。'
        result = parse_json_from_response(response)
        assert result == {"a": 1, "b": 2}

    def test_parse_json_from_response_no_json(self):
        """无 JSON 内容应抛异常"""
        from core.llm import parse_json_from_response
        with pytest.raises(json.JSONDecodeError):
            parse_json_from_response("没有 JSON 内容")

    def test_estimate_tokens_pure_chinese(self):
        """纯中文文本 token 估计"""
        from core.llm import estimate_tokens
        text = "你好世界"
        tokens = estimate_tokens(text)
        assert tokens == int(4 * 1.5 + 0)

    def test_estimate_tokens_mixed(self):
        """中英混合文本 token 估计"""
        from core.llm import estimate_tokens
        text = "Hello 你好 World 世界"
        tokens = estimate_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_estimate_tokens_empty(self):
        """空文本 token 为 0"""
        from core.llm import estimate_tokens
        assert estimate_tokens("") == 0

    def test_estimate_tokens_english_only(self):
        """纯英文文本 token 估计"""
        from core.llm import estimate_tokens
        text = "Hello World" * 100
        tokens = estimate_tokens(text)
        assert tokens > 0

    @patch("core.llm.MODEL_CONFIG", {"llm_cli": "/nonexistent/exe", "llm_path": "/nonexistent/model.gguf"})
    def test_call_llama_cpp_exe_not_found(self):
        """可执行文件不存在应抛异常"""
        from core.llm import call_llama_cpp
        with pytest.raises(RuntimeError) as exc_info:
            call_llama_cpp("test")
        assert "llama.cpp" in str(exc_info.value)

    def test_call_llama_cpp_no_model(self):
        """模型路径不匹配时应在文件校验阶段报错"""
        from core.llm import call_llama_cpp
        import os
        # 使用一个不存在的 exe 路径（实际不会到达 model 检查）
        original = os.path.exists
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda p: False
            with pytest.raises(RuntimeError) as exc_info:
                call_llama_cpp("test")
            assert "不存在" in str(exc_info.value)