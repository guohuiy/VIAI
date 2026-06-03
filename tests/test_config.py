"""
测试核心配置模块
"""

from core.config import (
    CHUNKING_CONFIG,
    MODEL_CONFIG,
    PROJECT_ROOT,
    RETRIEVAL_CONFIG,
    STORAGE_CONFIG,
    get_config,
)


class TestConfigStructure:
    """配置结构验证"""

    def test_project_root_exists(self):
        assert PROJECT_ROOT.exists()
        assert (PROJECT_ROOT / "core").exists()

    def test_model_config_keys(self):
        required_keys = {"llm_path", "llm_cli", "embed_path", "embed_cli",
                         "context_size", "max_tokens", "temperature"}
        assert required_keys.issubset(MODEL_CONFIG.keys())

    def test_model_config_values(self):
        assert MODEL_CONFIG["context_size"] > 0
        assert MODEL_CONFIG["max_tokens"] > 0
        assert 0 < MODEL_CONFIG["temperature"] <= 2.0

    def test_retrieval_config_keys(self):
        required_keys = {"top_k_vector", "top_k_fts", "top_k_rerank", "rrf_k", "max_context_tokens"}
        assert required_keys.issubset(RETRIEVAL_CONFIG.keys())

    def test_chunking_config_keys(self):
        required_keys = {"target_tokens", "overlap_tokens", "min_tokens"}
        assert required_keys.issubset(CHUNKING_CONFIG.keys())

    def test_chunking_config_values(self):
        assert CHUNKING_CONFIG["target_tokens"] > CHUNKING_CONFIG["overlap_tokens"]
        assert CHUNKING_CONFIG["min_tokens"] < CHUNKING_CONFIG["target_tokens"]

    def test_storage_config_paths(self):
        assert STORAGE_CONFIG["vector_db"].endswith("vector_db")
        assert STORAGE_CONFIG["sqlite"].endswith("library.db")

    def test_get_config_returns_all_sections(self):
        cfg = get_config()
        expected_sections = {"model", "retrieval", "chunking", "storage", "runtime"}
        assert expected_sections.issubset(cfg.keys())
