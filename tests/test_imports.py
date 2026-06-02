"""
Validate all core modules can be imported correctly
"""


class TestCoreImports:
    """Core module import tests"""

    def test_core_config_import(self):
        from core import config
        assert hasattr(config, "__file__")

    def test_storage_db_import(self):
        from storage import db
        assert hasattr(db, "__file__")

    def test_preprocessing_parsers_import(self):
        from preprocessing.parsers import base
        assert hasattr(base, "__file__")

    def test_retrieval_vector_store_import(self):
        from retrieval import vector_store
        assert hasattr(vector_store, "__file__")

    def test_agents_base_import(self):
        from agents import base
        assert hasattr(base, "__file__")

    def test_services_book_service_import(self):
        from services import book_service
        assert hasattr(book_service, "__file__")

    def test_generate_py_syntax(self):
        """Verify generate.py syntax (compile only, no execution)"""
        import py_compile
        py_compile.compile("generate.py", doraise=True)


class TestScriptImports:
    """Script module import tests"""

    def test_import_book_import(self):
        from scripts import import_book
        assert hasattr(import_book, "__file__")

    def test_build_index_import(self):
        from scripts import build_index
        assert hasattr(build_index, "__file__")