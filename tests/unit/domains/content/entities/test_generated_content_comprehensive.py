"""Comprehensive unit tests for GeneratedContent entity."""

import pytest
from datetime import datetime, timedelta
import json

from src.writeit.domains.content.entities.generated_content import GeneratedContent
from src.writeit.domains.content.value_objects.template_name import TemplateName
from src.writeit.domains.content.value_objects.style_name import StyleName
from src.writeit.domains.content.value_objects.content_type import ContentType
from src.writeit.domains.content.value_objects.content_format import ContentFormat
from src.writeit.domains.content.value_objects.content_id import ContentId

from tests.builders.content_builders import GeneratedContentBuilder


class TestGeneratedContent:
    """Test cases for GeneratedContent entity."""
    
    def test_generated_content_creation_with_valid_data(self):
        """Test creating generated content with valid data."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        assert isinstance(content.id, ContentId)
        assert isinstance(content.template_name, TemplateName)
        assert isinstance(content.content_type, ContentType)
        assert isinstance(content.format, ContentFormat)
        assert content.content_text.startswith("# Test Article")
        assert content.title == "Test Article"
        assert content.word_count > 0
        assert content.character_count > 0
        assert "article" in content.tags
        assert "markdown" in content.tags
        assert isinstance(content.created_at, datetime)
        assert isinstance(content.updated_at, datetime)
        assert content.version == "1.0.0"
        assert content.revision_count == 0
        assert content.approval_status is None
        assert content.published_at is None
    
    def test_generated_content_creation_with_custom_data(self):
        """Test creating generated content with custom data."""
        custom_content = "This is custom generated content for testing."
        custom_metadata = {
            "source": "test_generation",
            "quality_checked": True,
            "reviewer_notes": "Looks good"
        }
        
        content = (GeneratedContentBuilder()
                  .with_content_text(custom_content)
                  .with_template_name("custom-template")
                  .with_content_type(ContentType.blog_post())
                  .with_format(ContentFormat.markdown())
                  .with_title("Custom Content")
                  .with_summary("A custom piece of content")
                  .with_style_name("casual-style")
                  .with_metadata(custom_metadata)
                  .with_author("Test Creator")
                  .build())
        
        assert content.content_text == custom_content
        assert content.template_name.value == "custom-template"
        assert content.content_type == ContentType.blog_post()
        assert content.format == ContentFormat.markdown()
        assert content.title == "Custom Content"
        assert content.summary == "A custom piece of content"
        assert content.style_name.value == "casual-style"
        assert content.metadata == custom_metadata
        assert content.author == "Test Creator"
    
    def test_blog_post_content_creation(self):
        """Test creating blog post content."""
        content = GeneratedContentBuilder.blog_post("My Blog Post").build()
        
        assert content.content_type == ContentType.blog_post()
        assert content.title == "My Blog Post"
        assert "blog" in content.tags
        assert "post" in content.tags
        assert content.template_name.value == "blog-post-template"
        assert "my blog post" in content.content_text.lower()
    
    def test_technical_documentation_content_creation(self):
        """Test creating technical documentation content."""
        content = GeneratedContentBuilder.technical_doc("REST API Guide").build()
        
        assert content.content_type == ContentType.documentation()
        assert content.title == "REST API Guide"
        assert "technical" in content.tags
        assert "documentation" in content.tags
        assert "api" in content.tags
        assert content.template_name.value == "tech-doc-template"
        assert "```python" in content.content_text
        assert "```json" in content.content_text
    
    def test_email_content_creation(self):
        """Test creating email content."""
        content = GeneratedContentBuilder.email_content("Important Update").build()
        
        assert content.content_type == ContentType.email()
        assert content.format == ContentFormat.plain_text()
        assert content.title == "Important Update"
        assert "email" in content.tags
        assert "communication" in content.tags
        assert "Subject: Important Update" in content.content_text
        assert "Dear Recipient," in content.content_text
    
    def test_approved_content_creation(self):
        """Test creating approved content."""
        content = GeneratedContentBuilder.approved_content("Approved Article").build()
        
        assert content.approval_status == "approved"
        assert content.approved_by == "reviewer@example.com"
        assert content.approved_at is not None
        assert content.quality_metrics["overall_score"] == 8.5
        assert content.quality_metrics["readability_score"] == 9.0
        assert content.quality_metrics["seo_score"] == 7.5
    
    def test_published_content_creation(self):
        """Test creating published content."""
        content = GeneratedContentBuilder.published_content("Published Article").build()
        
        assert content.is_published() is True
        assert content.is_approved() is True
        assert content.published_at is not None
        assert isinstance(content.published_at, datetime)
    
    def test_content_with_generation_stats(self):
        """Test creating content with generation statistics."""
        content = GeneratedContentBuilder.with_generation_stats("Generated Article").build()
        
        assert content.pipeline_run_id == "run-12345"
        assert content.step_count == 3
        assert content.total_generation_time_seconds == 45.2
        assert content.llm_model_used == "gpt-4o-mini"
        assert content.total_tokens_used == 1250
        assert content.generation_cost == 0.025
    
    def test_generated_content_with_quality_metrics(self):
        """Test generated content with quality metrics."""
        quality_metrics = {
            "overall_score": 7.8,
            "readability_score": 8.2,
            "grammar_score": 9.1,
            "seo_score": 6.5,
            "tone_consistency": 8.7
        }
        
        content = (GeneratedContentBuilder.markdown_article()
                  .with_quality_metrics(quality_metrics)
                  .build())
        
        assert content.quality_metrics == quality_metrics
        assert content.get_quality_score() == 7.8
        assert content.get_readability_score() == 8.2
    
    def test_generated_content_with_feedback(self):
        """Test generated content with feedback."""
        feedback = [
            "Great introduction, very engaging",
            "Could use more examples in the middle section",
            "Conclusion ties everything together well"
        ]
        
        content = (GeneratedContentBuilder.markdown_article()
                  .with_feedback(feedback)
                  .build())
        
        assert content.feedback == feedback
        assert len(content.feedback) == 3
    
    def test_generated_content_with_parent_child_relationship(self):
        """Test generated content with parent-child relationship."""
        parent_id = ContentId.generate()
        
        content = (GeneratedContentBuilder.markdown_article()
                  .with_parent_content_id(parent_id)
                  .with_revision_count(2)
                  .with_version("1.0.2")
                  .build())
        
        assert content.parent_content_id == parent_id
        assert content.revision_count == 2
        assert content.version == "1.0.2"
    
    def test_generated_content_timestamps(self):
        """Test generated content timestamps."""
        now = datetime.now()
        content = GeneratedContentBuilder.markdown_article().build()
        
        # Created and updated should be close to now
        assert abs((content.created_at - now).total_seconds()) < 1
        assert abs((content.updated_at - now).total_seconds()) < 1
        
        # Test custom timestamps
        custom_time = datetime(2023, 8, 15, 14, 30, 0)
        content_with_custom = (GeneratedContentBuilder.markdown_article()
                              .with_timestamps(custom_time, custom_time)
                              .build())
        
        assert content_with_custom.created_at == custom_time
        assert content_with_custom.updated_at == custom_time


class TestGeneratedContentBusinessLogic:
    """Test business logic and invariants for GeneratedContent."""
    
    def test_update_content_creates_new_version(self):
        """Test updating content creates new version."""
        content = GeneratedContentBuilder.markdown_article().build()
        original_updated = content.updated_at
        
        # Wait a tiny bit to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        updated_content = content.update_content("Updated content text", "updater@example.com")
        
        assert updated_content.content_text == "Updated content text"
        assert updated_content.version == "1.0.1"  # Patch version incremented
        assert updated_content.revision_count == 1
        assert updated_content.author == "updater@example.com"
        assert updated_content.approval_status == "draft"  # Reset on update
        assert updated_content.updated_at > original_updated
        assert updated_content is not content  # Immutable
    
    def test_update_content_validation(self):
        """Test content update validation."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        with pytest.raises(ValueError, match="Content text cannot be empty"):
            content.update_content("")
        
        with pytest.raises(ValueError, match="Content text cannot be empty"):
            content.update_content("   ")
    
    def test_set_title_updates_content(self):
        """Test setting title updates content."""
        content = GeneratedContentBuilder.markdown_article().build()
        updated_content = content.set_title("New Article Title")
        
        assert updated_content.title == "New Article Title"
        assert updated_content is not content  # Immutable
    
    def test_set_title_validation(self):
        """Test title validation."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        with pytest.raises(ValueError, match="Title cannot be empty"):
            content.set_title("")
        
        with pytest.raises(ValueError, match="Title cannot be empty"):
            content.set_title("   ")
    
    def test_set_summary_updates_content(self):
        """Test setting summary updates content."""
        content = GeneratedContentBuilder.markdown_article().build()
        updated_content = content.set_summary("This is a comprehensive article summary.")
        
        assert updated_content.summary == "This is a comprehensive article summary."
        assert updated_content is not content  # Immutable
    
    def test_set_summary_validation(self):
        """Test summary validation."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        with pytest.raises(ValueError, match="Summary cannot be empty"):
            content.set_summary("")
        
        with pytest.raises(ValueError, match="Summary cannot be empty"):
            content.set_summary("   ")
    
    def test_add_quality_metric_updates_content(self):
        """Test adding quality metric updates content."""
        content = GeneratedContentBuilder.markdown_article().build()
        updated_content = content.add_quality_metric("clarity_score", 8.9)
        
        assert updated_content.quality_metrics["clarity_score"] == 8.9
        assert updated_content is not content  # Immutable
    
    def test_add_quality_metric_validation(self):
        """Test quality metric validation."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        with pytest.raises(ValueError, match="Metric name cannot be empty"):
            content.add_quality_metric("", 5.0)
        
        with pytest.raises(ValueError, match="Metric name cannot be empty"):
            content.add_quality_metric("   ", 5.0)
    
    def test_set_approval_status_updates_content(self):
        """Test setting approval status updates content."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        # Test setting to under review
        under_review = content.set_approval_status("under_review", "reviewer@example.com")
        assert under_review.approval_status == "under_review"
        assert under_review.approved_by == "reviewer@example.com"
        assert under_review.approved_at is None
        
        # Test approving
        approved = under_review.set_approval_status("approved", "approver@example.com")
        assert approved.approval_status == "approved"
        assert approved.approved_by == "approver@example.com"
        assert approved.approved_at is not None
        assert approved.is_approved() is True
        
        # Test rejecting
        rejected = under_review.set_approval_status("rejected", "reviewer@example.com")
        assert rejected.approval_status == "rejected"
        assert rejected.approved_at is not None
        assert rejected.is_approved() is False
    
    def test_set_approval_status_validation(self):
        """Test approval status validation."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        with pytest.raises(ValueError, match="Invalid approval status"):
            content.set_approval_status("invalid_status")
        
        # Valid statuses should work
        valid_statuses = ["draft", "under_review", "approved", "rejected"]
        for status in valid_statuses:
            updated = content.set_approval_status(status)
            assert updated.approval_status == status
    
    def test_add_feedback_updates_content(self):
        """Test adding feedback updates content."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        # Add feedback without author
        with_feedback = content.add_feedback("This needs improvement in section 2")
        assert "This needs improvement in section 2" in with_feedback.feedback
        
        # Add feedback with author
        with_author_feedback = with_feedback.add_feedback("Great work overall!", "reviewer@example.com")
        assert "[reviewer@example.com] Great work overall!" in with_author_feedback.feedback
        assert len(with_author_feedback.feedback) == 2
    
    def test_add_feedback_validation(self):
        """Test feedback validation."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        with pytest.raises(ValueError, match="Feedback cannot be empty"):
            content.add_feedback("")
        
        with pytest.raises(ValueError, match="Feedback cannot be empty"):
            content.add_feedback("   ")
    
    def test_add_tag_updates_content(self):
        """Test adding tag updates content."""
        content = GeneratedContentBuilder.markdown_article().build()
        original_count = len(content.tags)
        
        updated_content = content.add_tag("Featured")
        
        assert len(updated_content.tags) == original_count + 1
        assert "featured" in updated_content.tags  # Normalized to lowercase
        assert updated_content is not content  # Immutable
    
    def test_add_tag_prevents_duplicates(self):
        """Test adding duplicate tag doesn't change content."""
        content = GeneratedContentBuilder.markdown_article().build()
        existing_tag = content.tags[0]
        
        updated_content = content.add_tag(existing_tag.upper())  # Different case
        
        assert updated_content is content  # No change
        assert len(updated_content.tags) == len(content.tags)
    
    def test_add_tag_validation(self):
        """Test tag validation."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        with pytest.raises(ValueError, match="Tag cannot be empty"):
            content.add_tag("")
        
        with pytest.raises(ValueError, match="Tag cannot be empty"):
            content.add_tag("   ")
    
    def test_remove_tag_updates_content(self):
        """Test removing tag updates content."""
        content = (GeneratedContentBuilder.markdown_article()
                  .with_tags(["article", "markdown", "featured"])
                  .build())
        
        updated_content = content.remove_tag("featured")
        
        assert "featured" not in updated_content.tags
        assert "article" in updated_content.tags
        assert "markdown" in updated_content.tags
        assert updated_content is not content  # Immutable
    
    def test_remove_nonexistent_tag_no_change(self):
        """Test removing non-existent tag doesn't change content."""
        content = GeneratedContentBuilder.markdown_article().build()
        original_count = len(content.tags)
        
        updated_content = content.remove_tag("nonexistent")
        
        assert updated_content is content  # No change
        assert len(updated_content.tags) == original_count
    
    def test_set_generation_metadata_updates_content(self):
        """Test setting generation metadata updates content."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        updated_content = content.set_generation_metadata(
            pipeline_run_id="run-456",
            step_count=5,
            generation_time=120.5,
            model_used="gpt-4",
            tokens_used=2000,
            cost=0.05
        )
        
        assert updated_content.pipeline_run_id == "run-456"
        assert updated_content.step_count == 5
        assert updated_content.total_generation_time_seconds == 120.5
        assert updated_content.llm_model_used == "gpt-4"
        assert updated_content.total_tokens_used == 2000
        assert updated_content.generation_cost == 0.05
        assert updated_content is not content  # Immutable
    
    def test_publish_content_requires_approval(self):
        """Test publishing content requires approval."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        # Should fail without approval
        with pytest.raises(ValueError, match="Content must be approved before publishing"):
            content.publish("publisher@example.com")
        
        # Should work after approval
        approved_content = content.set_approval_status("approved", "approver@example.com")
        published_content = approved_content.publish("publisher@example.com")
        
        assert published_content.is_published() is True
        assert published_content.published_at is not None
        assert published_content.author == "publisher@example.com"
    
    def test_create_revision_generates_new_content(self):
        """Test creating revision generates new content entity."""
        content = GeneratedContentBuilder.markdown_article().build()
        original_id = content.id
        
        revision = content.create_revision("Revised content text", "editor@example.com")
        
        assert revision.id != original_id  # New ID
        assert revision.content_text == "Revised content text"
        assert revision.parent_content_id == original_id
        assert revision.revision_count == 1
        assert revision.author == "editor@example.com"
        assert revision.approval_status == "draft"
        assert revision.approved_by is None
        assert revision.approved_at is None
        assert revision.published_at is None
    
    def test_create_revision_validation(self):
        """Test revision creation validation."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        with pytest.raises(ValueError, match="Content text cannot be empty"):
            content.create_revision("")
        
        with pytest.raises(ValueError, match="Content text cannot be empty"):
            content.create_revision("   ")
    
    def test_get_generation_efficiency(self):
        """Test generation efficiency calculation."""
        content = (GeneratedContentBuilder.markdown_article()
                  .with_generation_metadata(generation_time=30.0)
                  .with_word_count(150)
                  .build())
        
        efficiency = content.get_generation_efficiency()
        assert efficiency == 5.0  # 150 words / 30 seconds
        
        # Test with no generation time
        no_time_content = GeneratedContentBuilder.markdown_article().build()
        assert no_time_content.get_generation_efficiency() is None
    
    def test_get_cost_per_word(self):
        """Test cost per word calculation."""
        content = (GeneratedContentBuilder.markdown_article()
                  .with_generation_metadata(cost=0.10)
                  .with_word_count(100)
                  .build())
        
        cost_per_word = content.get_cost_per_word()
        assert cost_per_word == 0.001  # $0.10 / 100 words
        
        # Test with no cost or word count
        no_cost_content = GeneratedContentBuilder.markdown_article().build()
        assert no_cost_content.get_cost_per_word() is None
    
    def test_create_class_method(self):
        """Test GeneratedContent.create class method."""
        template_name = TemplateName("test-template")
        style_name = StyleName("professional")
        
        content = GeneratedContent.create(
            content_text="This is test content created via class method.",
            template_name=template_name,
            content_type=ContentType.article(),
            format=ContentFormat.markdown(),
            title="Test Article",
            summary="A test article summary",
            style_name=style_name,
            author="Creator",
            pipeline_run_id="run-789"
        )
        
        assert content.content_text == "This is test content created via class method."
        assert content.template_name == template_name
        assert content.content_type == ContentType.article()
        assert content.format == ContentFormat.markdown()
        assert content.title == "Test Article"
        assert content.summary == "A test article summary"
        assert content.style_name == style_name
        assert content.author == "Creator"
        assert content.pipeline_run_id == "run-789"
        assert content.approval_status == "draft"
        assert content.word_count > 0  # Auto-calculated
        assert content.character_count > 0  # Auto-calculated


class TestGeneratedContentEdgeCases:
    """Test edge cases and error conditions for GeneratedContent."""
    
    def test_generated_content_with_empty_content_validation(self):
        """Test generated content validation with empty content."""
        with pytest.raises(ValueError, match="Content text cannot be empty"):
            GeneratedContent(
                id=ContentId.generate(),
                content_text="",
                template_name=TemplateName("test"),
                content_type=ContentType.article(),
                format=ContentFormat.markdown(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        with pytest.raises(ValueError, match="Content text cannot be empty"):
            GeneratedContent(
                id=ContentId.generate(),
                content_text="   ",
                template_name=TemplateName("test"),
                content_type=ContentType.article(),
                format=ContentFormat.markdown(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_generated_content_with_unicode_content(self):
        """Test generated content with unicode content."""
        unicode_content = """
        # Artïçlë Tïtlë 🌟
        
        Thïs ïs üñïçödë çöñtëñt wïth spëçïål çhàràçtërs àñd ëmöjïs.
        
        ## Sëçtïön Öñë 📝
        Hërë's sömë détàïlëd ïñförmàtïöñ ïñ müłtïplë làñgüàgës.
        
        ## Çöñçlüsïöñ 🎉
        Üñïçödë süppört ïs ïmpörtàñt för ïñtërnàtïönàł çöñtëñt.
        """
        
        content = (GeneratedContentBuilder()
                  .with_content_text(unicode_content)
                  .with_title("Üñïçödë Artïçlë 🌍")
                  .with_summary("Àñ àrtïçlë wïth üñïçödë çhàràçtërs")
                  .build())
        
        assert content.content_text == unicode_content
        assert content.title == "Üñïçödë Artïçlë 🌍"
        assert content.summary == "Àñ àrtïçlë wïth üñïçödë çhàràçtërs"
        assert "🌟" in content.content_text
        assert "🎉" in content.content_text
    
    def test_generated_content_with_special_characters_in_metadata(self):
        """Test generated content with special characters in metadata."""
        special_metadata = {
            "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
            "paths": ["/special/path", "C:\\Windows\\Path"],
            "unicode": "Spëçîál metadata 🎉",
            "nested": {"key": "value with émojis 😊"}
        }
        
        content = (GeneratedContentBuilder.markdown_article()
                  .with_metadata(special_metadata)
                  .build())
        
        assert content.metadata == special_metadata
        assert "!@#$%^&*()" in content.metadata["special_chars"]
        assert "🎉" in content.metadata["unicode"]
        assert "😊" in content.metadata["nested"]["key"]
    
    def test_generated_content_metadata_serialization(self):
        """Test that generated content metadata is JSON serializable."""
        content = GeneratedContentBuilder.markdown_article().build()
        
        # Basic metadata should be JSON serializable
        try:
            json.dumps(content.metadata)
        except (TypeError, ValueError) as e:
            pytest.fail(f"GeneratedContent metadata not serializable: {e}")
    
    def test_generated_content_with_large_content(self):
        """Test generated content with large content."""
        large_content = "This is a very long article. " * 1000  # ~30KB
        
        content = (GeneratedContentBuilder()
                  .with_content_text(large_content)
                  .with_title("Large Article")
                  .build())
        
        assert len(content.content_text) > 25000
        assert content.word_count > 5000
        assert content.character_count > 25000
        assert content.title == "Large Article"
    
    def test_generated_content_post_init_validation(self):
        """Test GeneratedContent post-init validation."""
        with pytest.raises(TypeError, match="Generated content ID must be a ContentId"):
            GeneratedContent(
                id="invalid_id",  # type: ignore
                content_text="Test content",
                template_name=TemplateName("test"),
                content_type=ContentType.article(),
                format=ContentFormat.markdown(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        with pytest.raises(TypeError, match="Template name must be a TemplateName"):
            GeneratedContent(
                id=ContentId.generate(),
                content_text="Test content",
                template_name="invalid_template",  # type: ignore
                content_type=ContentType.article(),
                format=ContentFormat.markdown(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        with pytest.raises(TypeError, match="Content type must be a ContentType"):
            GeneratedContent(
                id=ContentId.generate(),
                content_text="Test content",
                template_name=TemplateName("test"),
                content_type="invalid_type",  # type: ignore
                format=ContentFormat.markdown(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        with pytest.raises(TypeError, match="Content format must be a ContentFormat"):
            GeneratedContent(
                id=ContentId.generate(),
                content_text="Test content",
                template_name=TemplateName("test"),
                content_type=ContentType.article(),
                format="invalid_format",  # type: ignore
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        with pytest.raises(TypeError, match="Style name must be a StyleName"):
            GeneratedContent(
                id=ContentId.generate(),
                content_text="Test content",
                template_name=TemplateName("test"),
                content_type=ContentType.article(),
                format=ContentFormat.markdown(),
                style_name="invalid_style",  # type: ignore
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_generated_content_string_representations(self):
        """Test string representations of GeneratedContent."""
        # Draft content
        draft_content = GeneratedContentBuilder.markdown_article("Test Article").build()
        str_repr = str(draft_content)
        expected_words = len(draft_content.content_text.split())
        assert f"GeneratedContent(article-template, {expected_words} words, draft)" == str_repr
        
        # Approved content
        approved_content = (GeneratedContentBuilder.markdown_article("Approved Article")
                           .with_approval_status("approved", "approver@example.com")
                           .build())
        str_repr = str(approved_content)
        expected_words = len(approved_content.content_text.split())
        assert f"GeneratedContent(article-template, {expected_words} words, approved)" == str_repr
        
        # Test repr
        repr_str = repr(draft_content)
        assert "GeneratedContent(id=" in repr_str
        assert "template=article-template" in repr_str
        assert f"words={expected_words}" in repr_str
        assert "status=draft" in repr_str
    
    def test_generated_content_immutability(self):
        """Test generated content immutability after creation."""
        content = GeneratedContentBuilder.markdown_article().build()
        original_text = content.content_text
        original_status = content.approval_status
        
        # Direct modification should not be possible (frozen dataclass)
        with pytest.raises(AttributeError):
            content.content_text = "Modified content"  # type: ignore
        
        with pytest.raises(AttributeError):
            content.approval_status = "approved"  # type: ignore
        
        # Values should remain unchanged
        assert content.content_text == original_text
        assert content.approval_status == original_status
    
    def test_word_and_character_count_auto_calculation(self):
        """Test automatic word and character count calculation."""
        content_text = "This is a test sentence with exactly ten words total."
        
        content = (GeneratedContentBuilder()
                  .with_content_text(content_text)
                  .build())
        
        # Should auto-calculate if not provided
        assert content.word_count == 10
        assert content.character_count == len(content_text)
        
        # Should use provided values if given
        content_with_counts = (GeneratedContentBuilder()
                              .with_content_text(content_text)
                              .with_word_count(15)  # Override auto-calculation
                              .with_character_count(100)  # Override auto-calculation
                              .build())
        
        assert content_with_counts.word_count == 15
        assert content_with_counts.character_count == 100