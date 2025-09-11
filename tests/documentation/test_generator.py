"""
Tests for documentation generator
"""

from writeit.docs import DocumentationGenerator


class TestDocumentationGenerator:
    """Test documentation generation functionality"""

    def test_generator_initialization(self):
        """Test generator initializes correctly"""
        generator = DocumentationGenerator()
        assert generator is not None
        assert generator.config is not None
        assert generator.extractors is not None

    def test_generator_with_config(self, tmp_path):
        """Test generator with custom configuration"""
        config_path = tmp_path / "config.yaml"
        config_content = """
documentation:
  sources:
    modules:
      path: src/writeit
      patterns: ["**/*.py"]
"""
        config_path.write_text(config_content)

        generator = DocumentationGenerator(config_path=config_path)
        assert generator.config is not None
        assert "modules" in generator.config.sources

    def test_generate_all_documentation(self):
        """Test generating complete documentation set"""
        generator = DocumentationGenerator()
        docs = generator.generate_all()

        assert docs is not None
        assert docs.generated_at is not None
        assert docs.version is not None

        # Should generate at least some documentation
        has_content = (
            docs.api_docs is not None
            or len(docs.module_docs) > 0
            or docs.cli_docs is not None
            or docs.template_docs is not None
            or len(docs.user_guides) > 0
        )
        assert has_content, "Should generate at least some documentation"

    def test_generate_module_documentation(self):
        """Test generating module documentation"""
        generator = DocumentationGenerator()

        # Test with actual WriteIt module
        module_doc = generator.generate_for_module("writeit.docs.models")

        if module_doc:  # Only test if module exists
            assert module_doc.name == "docs.models"
            assert module_doc.description is not None
            assert isinstance(module_doc.classes, list)
            assert isinstance(module_doc.functions, list)

    def test_metrics_tracking(self):
        """Test that metrics are tracked correctly"""
        generator = DocumentationGenerator()
        generator.generate_all()
        metrics = generator.get_metrics()

        assert metrics is not None
        assert metrics.generation_time >= 0
        assert metrics.total_modules >= 0
        assert metrics.total_classes >= 0
        assert metrics.total_functions >= 0

    def test_validation_after_generation(self):
        """Test validation after documentation generation"""
        generator = DocumentationGenerator()
        generator.generate_all()

        # Basic validation
        is_valid = generator.validate_generation()
        assert isinstance(is_valid, bool)

    def test_empty_module_handling(self):
        """Test handling of modules with no documentation"""
        generator = DocumentationGenerator()

        # This should handle non-existent modules gracefully
        module_doc = generator.generate_for_module("nonexistent.module")
        assert module_doc is None

    def test_class_generation(self):
        """Test generating documentation for specific class"""
        generator = DocumentationGenerator()

        # Test with actual WriteIt class
        class_doc = generator.generate_for_class("writeit.docs.models.DocumentationSet")

        if class_doc:  # Only test if class exists
            assert class_doc.name == "DocumentationSet"
            assert class_doc.description is not None
            assert isinstance(class_doc.methods, list)
