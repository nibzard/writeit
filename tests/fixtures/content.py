"""Content domain entity fixtures for testing.

Provides comprehensive test fixtures for content domain entities including
templates, style primers, generated content, and validation scenarios.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List, Optional

from writeit.domains.content.entities.template import Template
from writeit.domains.content.entities.style_primer import StylePrimer
from writeit.domains.content.entities.generated_content import GeneratedContent
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.style_name import StyleName
from writeit.domains.content.value_objects.content_type import ContentType
from writeit.domains.content.value_objects.content_format import ContentFormat
from writeit.domains.content.value_objects.content_length import ContentLength
from writeit.domains.content.value_objects.validation_rule import ValidationRule


# ============================================================================
# Basic Content Entity Fixtures
# ============================================================================

@pytest.fixture
def content_id_fixture():
    """Valid content ID for testing."""
    return ContentId.generate()

@pytest.fixture
def template_name_fixture():
    """Valid template name for testing."""
    return TemplateName.from_user_input("test-template")

@pytest.fixture
def style_name_fixture():
    """Valid style name for testing."""
    return StyleName.from_user_input("professional")

@pytest.fixture
def content_type_fixture():
    """Valid content type for testing."""
    return ContentType.article()

@pytest.fixture
def content_format_fixture():
    """Valid content format for testing."""
    return ContentFormat.markdown()

@pytest.fixture
def content_length_fixture():
    """Valid content length constraints."""
    return ContentLength.create(min_words=100, max_words=1000, target_words=500)

@pytest.fixture
def validation_rule_fixture():
    """Valid validation rule for testing."""
    return ValidationRule.word_count_range(100, 1000)

@pytest.fixture
def template_fixture():
    """Valid template with comprehensive YAML content."""
    yaml_content = """metadata:
  name: "Article Template"
  description: "Template for generating structured articles"
  version: "1.0.0"
  author: "Test Author"

defaults:
  model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 2000

inputs:
  topic:
    type: text
    label: "Article Topic"
    required: true
    placeholder: "Enter the main topic..."
    help: "The primary subject matter for the article"
    max_length: 100
    validation:
      min_length: 3

  style:
    type: choice
    label: "Writing Style"
    required: true
    default: "formal"
    options:
      - label: "Formal"
        value: "formal"
      - label: "Casual" 
        value: "casual"
      - label: "Technical"
        value: "technical"

  word_count:
    type: number
    label: "Target Word Count"
    required: false
    default: 800
    validation:
      min: 200
      max: 2000

steps:
  outline:
    name: "Create Outline"
    description: "Generate article outline and structure"
    type: llm_generate
    prompt_template: |
      Create a detailed outline for an article about "{{ inputs.topic }}" 
      in {{ inputs.style }} style. Target length: {{ inputs.word_count }} words.
      
      Include:
      - Introduction hook
      - 3-5 main sections with subsections
      - Key points to cover
      - Conclusion summary
    model_preference: ["{{ defaults.model }}"]

  content:
    name: "Write Content"
    description: "Generate full article content"
    type: llm_generate
    depends_on: ["outline"]
    prompt_template: |
      Based on this outline:
      {{ steps.outline }}
      
      Write a comprehensive {{ inputs.style }} article about "{{ inputs.topic }}".
      Target length: {{ inputs.word_count }} words.
      
      Requirements:
      - Engaging introduction
      - Well-structured body following the outline
      - Smooth transitions between sections
      - Informative and actionable content
      - Strong conclusion
    model_preference: ["{{ defaults.model }}"]

  review:
    name: "Review and Polish"
    description: "Review and improve the content"
    type: llm_generate
    depends_on: ["content"]
    prompt_template: |
      Review and improve this article:
      {{ steps.content }}
      
      Focus on:
      - Grammar and clarity
      - Flow and readability
      - Factual accuracy
      - Style consistency ({{ inputs.style }})
      - Meeting target word count ({{ inputs.word_count }})
      
      Provide the polished version.
    model_preference: ["{{ defaults.model }}"]
"""

    return Template.create(
        name=TemplateName.from_user_input("article-template"),
        content_type=ContentType.article(),
        yaml_content=yaml_content,
        author="Test Author",
        description="Comprehensive article generation template",
        tags=["article", "content", "structured"],
        output_format=ContentFormat.markdown(),
        content_length=ContentLength.create(500, 2000, 800),
        validation_rules=[
            ValidationRule.word_count_range(500, 2000),
            ValidationRule.readability_score(8.0)
        ]
    )

@pytest.fixture
def style_primer_fixture():
    """Valid style primer with comprehensive guidelines."""
    return StylePrimer.create(
        name=StyleName.from_user_input("professional-tech"),
        description="Professional technical writing style for software documentation",
        tone="professional",
        voice="third_person",
        writing_style="technical",
        target_audience="software developers",
        language="en",
        author="Content Team"
    ).add_guideline(
        "Use clear, concise language without jargon"
    ).add_guideline(
        "Include practical examples and code snippets"
    ).add_guideline(
        "Structure content with clear headings and bullet points"
    ).set_formatting_preference(
        "code_style", "markdown"
    ).set_vocabulary_preference(
        "terminology", "industry_standard"
    ).add_example(
        "Instead of 'The system performs data processing', use 'The API processes user data in real-time'"
    ).add_applicable_content_type(
        ContentType.documentation()
    ).add_tag("technical").add_tag("professional")

@pytest.fixture
def generated_content_fixture():
    """Valid generated content with metadata."""
    content_text = """# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. This transformative technology has revolutionized various industries and continues to shape our digital future.

## Core Concepts

### Supervised Learning
Supervised learning uses labeled training data to learn a mapping from inputs to outputs. Common applications include:
- Classification problems (email spam detection)
- Regression problems (price prediction)

### Unsupervised Learning
Unsupervised learning finds hidden patterns in data without labeled examples:
- Clustering (customer segmentation)
- Dimensionality reduction (data visualization)

### Reinforcement Learning
Reinforcement learning involves training agents to make decisions through trial and error:
- Game playing (AlphaGo, chess)
- Autonomous systems (self-driving cars)

## Applications

Machine learning powers many technologies we use daily:
- Recommendation systems (Netflix, Amazon)
- Voice assistants (Siri, Alexa)
- Image recognition (photo tagging)
- Natural language processing (translation, chatbots)

## Getting Started

To begin your machine learning journey:
1. Learn Python and key libraries (scikit-learn, pandas, numpy)
2. Understand statistics and linear algebra fundamentals
3. Practice with real datasets on platforms like Kaggle
4. Take online courses from reputable institutions

## Conclusion

Machine learning represents one of the most exciting frontiers in technology. As algorithms become more sophisticated and data more abundant, the potential applications continue to expand. Whether you're a developer, business professional, or curious learner, understanding machine learning concepts will become increasingly valuable in our data-driven world.
"""

    return GeneratedContent.create(
        content_text=content_text,
        template_name=TemplateName.from_user_input("article-template"),
        content_type=ContentType.article(),
        format=ContentFormat.markdown(),
        title="Introduction to Machine Learning",
        summary="Comprehensive overview of machine learning concepts, applications, and getting started guide",
        author="AI Assistant",
        pipeline_run_id="run-12345"
    ).set_quality_score(0.85).add_validation_result(
        ValidationRule.word_count_range(200, 1000), True, "Word count: 347"
    ).add_validation_result(
        ValidationRule.readability_score(8.0), True, "Readability score: 8.2"
    ).add_tag("machine-learning").add_tag("educational").publish()


# ============================================================================
# Content Type Variants
# ============================================================================

@pytest.fixture
def blog_post_template():
    """Blog post template with casual tone."""
    yaml_content = """metadata:
  name: "Blog Post Template"
  description: "Template for engaging blog posts"
  version: "1.0.0"

defaults:
  model: "gpt-4o-mini"
  tone: "casual"

inputs:
  topic:
    type: text
    label: "Blog Topic"
    required: true
  
  target_audience:
    type: text
    label: "Target Audience"
    required: true
    default: "general readers"

steps:
  hook:
    name: "Create Hook"
    description: "Generate engaging opening"
    type: llm_generate
    prompt_template: |
      Create an engaging blog post opening about "{{ inputs.topic }}" 
      for {{ inputs.target_audience }}. Use a {{ defaults.tone }} tone.
    
  content:
    name: "Write Blog Content"
    description: "Generate main blog content"
    type: llm_generate
    depends_on: ["hook"]
    prompt_template: |
      Continue this blog post about "{{ inputs.topic }}":
      {{ steps.hook }}
      
      Write engaging, {{ defaults.tone }} content for {{ inputs.target_audience }}.
      Include personal anecdotes, practical tips, and a conversational style.
"""

    return Template.create(
        name=TemplateName.from_user_input("blog-post-template"),
        content_type=ContentType.blog_post(),
        yaml_content=yaml_content,
        author="Content Creator",
        tags=["blog", "casual", "engaging"],
        output_format=ContentFormat.markdown(),
        content_length=ContentLength.create(300, 1500, 800)
    )

@pytest.fixture
def email_template():
    """Email template for business communication."""
    yaml_content = """metadata:
  name: "Business Email Template"
  description: "Template for professional business emails"
  version: "1.0.0"

defaults:
  model: "gpt-4o-mini"
  tone: "professional"

inputs:
  recipient_name:
    type: text
    label: "Recipient Name"
    required: true
  
  purpose:
    type: choice
    label: "Email Purpose"
    required: true
    options:
      - label: "Follow-up"
        value: "follow_up"
      - label: "Introduction"
        value: "introduction"
      - label: "Request"
        value: "request"
  
  key_points:
    type: text
    label: "Key Points"
    required: true
    help: "Main points to communicate"

steps:
  subject:
    name: "Generate Subject Line"
    description: "Create compelling subject line"
    type: llm_generate
    prompt_template: |
      Create a professional email subject line for a {{ inputs.purpose }} email
      to {{ inputs.recipient_name }}. Key points: {{ inputs.key_points }}
  
  body:
    name: "Write Email Body"
    description: "Generate email content"
    type: llm_generate
    depends_on: ["subject"]
    prompt_template: |
      Write a professional email to {{ inputs.recipient_name }}.
      Purpose: {{ inputs.purpose }}
      Subject: {{ steps.subject }}
      
      Include these key points: {{ inputs.key_points }}
      
      Use a {{ defaults.tone }} tone, be concise and clear.
"""

    return Template.create(
        name=TemplateName.from_user_input("business-email-template"),
        content_type=ContentType.email(),
        yaml_content=yaml_content,
        author="Business Writer",
        tags=["email", "business", "professional"],
        output_format=ContentFormat.plain_text(),
        content_length=ContentLength.create(50, 300, 150)
    )

@pytest.fixture
def social_media_template():
    """Social media post template."""
    yaml_content = """metadata:
  name: "Social Media Post Template"
  description: "Template for engaging social media content"
  version: "1.0.0"

defaults:
  model: "gpt-4o-mini"
  tone: "engaging"

inputs:
  platform:
    type: choice
    label: "Social Platform"
    required: true
    options:
      - label: "Twitter"
        value: "twitter"
      - label: "LinkedIn"
        value: "linkedin"
      - label: "Facebook"
        value: "facebook"
  
  topic:
    type: text
    label: "Post Topic"
    required: true
  
  include_hashtags:
    type: boolean
    label: "Include Hashtags"
    default: true

steps:
  content:
    name: "Generate Post"
    description: "Create social media content"
    type: llm_generate
    prompt_template: |
      Create a {{ inputs.platform }} post about "{{ inputs.topic }}".
      
      Platform requirements:
      - Twitter: 280 characters max, conversational
      - LinkedIn: Professional tone, 1-3 paragraphs
      - Facebook: Engaging, personal, encourage interaction
      
      {% if inputs.include_hashtags %}
      Include relevant hashtags.
      {% endif %}
      
      Use {{ defaults.tone }} tone appropriate for the platform.
"""

    return Template.create(
        name=TemplateName.from_user_input("social-media-template"),
        content_type=ContentType.social_media(),
        yaml_content=yaml_content,
        author="Social Media Manager",
        tags=["social", "marketing", "engagement"],
        output_format=ContentFormat.plain_text(),
        content_length=ContentLength.create(10, 500, 100)
    )


# ============================================================================
# Style Primer Variants
# ============================================================================

@pytest.fixture
def casual_style_primer():
    """Casual writing style primer."""
    return StylePrimer.create(
        name=StyleName.from_user_input("casual-friendly"),
        description="Casual, friendly writing style for general audiences",
        tone="casual",
        voice="second_person",
        writing_style="conversational",
        target_audience="general readers",
        language="en"
    ).add_guideline(
        "Use contractions and informal language"
    ).add_guideline(
        "Address the reader directly with 'you'"
    ).add_guideline(
        "Include personal anecdotes and examples"
    ).add_example(
        "Instead of 'One should consider', use 'You might want to think about'"
    ).add_tag("casual").add_tag("friendly")

@pytest.fixture
def academic_style_primer():
    """Academic writing style primer."""
    return StylePrimer.create(
        name=StyleName.from_user_input("academic-formal"),
        description="Formal academic writing style for research and education",
        tone="formal",
        voice="third_person",
        writing_style="academic",
        target_audience="researchers and students",
        language="en"
    ).add_guideline(
        "Use formal language and avoid contractions"
    ).add_guideline(
        "Support claims with evidence and citations"
    ).add_guideline(
        "Use passive voice appropriately"
    ).add_guideline(
        "Structure arguments logically with clear transitions"
    ).add_example(
        "Research indicates that machine learning algorithms demonstrate improved performance when..."
    ).add_tag("academic").add_tag("formal").add_tag("research")

@pytest.fixture
def marketing_style_primer():
    """Marketing copy style primer."""
    return StylePrimer.create(
        name=StyleName.from_user_input("marketing-persuasive"),
        description="Persuasive marketing style for promotional content",
        tone="enthusiastic",
        voice="second_person",
        writing_style="persuasive",
        target_audience="potential customers",
        language="en"
    ).add_guideline(
        "Use action-oriented language and strong verbs"
    ).add_guideline(
        "Focus on benefits rather than features"
    ).add_guideline(
        "Create urgency and encourage action"
    ).add_guideline(
        "Use emotional triggers and power words"
    ).add_example(
        "Transform your workflow today with our revolutionary AI-powered solution!"
    ).add_tag("marketing").add_tag("persuasive").add_tag("sales")


# ============================================================================
# Generated Content Variants
# ============================================================================

@pytest.fixture
def draft_generated_content():
    """Generated content in draft state."""
    return GeneratedContent.create(
        content_text="# Draft Article\n\nThis is a draft article that needs review.",
        template_name=TemplateName.from_user_input("article-template"),
        content_type=ContentType.article(),
        format=ContentFormat.markdown(),
        title="Draft Article"
    ).set_quality_score(0.6)

@pytest.fixture
def published_generated_content():
    """Generated content that has been published."""
    content = GeneratedContent.create(
        content_text="# Published Article\n\nThis is a high-quality published article.",
        template_name=TemplateName.from_user_input("article-template"),
        content_type=ContentType.article(),
        format=ContentFormat.markdown(),
        title="Published Article",
        author="Content Creator"
    ).set_quality_score(0.9).publish()
    
    return content

@pytest.fixture
def rejected_generated_content():
    """Generated content that has been rejected."""
    return GeneratedContent.create(
        content_text="# Rejected Article\n\nThis content did not meet quality standards.",
        template_name=TemplateName.from_user_input("article-template"),
        content_type=ContentType.article(),
        format=ContentFormat.markdown(),
        title="Rejected Article"
    ).set_quality_score(0.3).reject("Content quality below threshold")


# ============================================================================
# Validation Rule Variants
# ============================================================================

@pytest.fixture
def validation_rule_variants():
    """Different types of validation rules."""
    return {
        "word_count": ValidationRule.word_count_range(100, 1000),
        "character_count": ValidationRule.character_count_range(500, 5000),
        "readability": ValidationRule.readability_score(8.0),
        "sentiment": ValidationRule.sentiment_range(-0.1, 0.1),
        "keyword_density": ValidationRule.keyword_density("AI", 0.02, 0.05),
        "plagiarism": ValidationRule.plagiarism_threshold(0.15),
        "grammar": ValidationRule.grammar_score(0.9),
        "tone_consistency": ValidationRule.tone_consistency("professional")
    }


# ============================================================================
# Complex Content Scenarios
# ============================================================================

@pytest.fixture
def content_with_validation_results():
    """Generated content with comprehensive validation results."""
    content = GeneratedContent.create(
        content_text="# AI in Healthcare\n\nArtificial intelligence is transforming healthcare...",
        template_name=TemplateName.from_user_input("healthcare-template"),
        content_type=ContentType.article(),
        format=ContentFormat.markdown(),
        title="AI in Healthcare"
    )
    
    # Add validation results
    validation_rules = [
        (ValidationRule.word_count_range(200, 800), True, "Word count: 456"),
        (ValidationRule.readability_score(8.0), True, "Readability: 8.3"), 
        (ValidationRule.sentiment_range(-0.1, 0.1), True, "Sentiment: 0.05"),
        (ValidationRule.grammar_score(0.9), False, "Grammar score: 0.85"),
        (ValidationRule.plagiarism_threshold(0.15), True, "Plagiarism: 0.03")
    ]
    
    for rule, passed, message in validation_rules:
        content = content.add_validation_result(rule, passed, message)
    
    return content.set_quality_score(0.82)

@pytest.fixture
def multilingual_content():
    """Generated content in multiple languages."""
    return {
        "english": GeneratedContent.create(
            content_text="# Welcome\n\nWelcome to our platform.",
            template_name=TemplateName.from_user_input("welcome-template"),
            content_type=ContentType.article(),
            format=ContentFormat.markdown(),
            title="Welcome"
        ).set_language("en"),
        
        "spanish": GeneratedContent.create(
            content_text="# Bienvenido\n\nBienvenido a nuestra plataforma.",
            template_name=TemplateName.from_user_input("welcome-template"),
            content_type=ContentType.article(),
            format=ContentFormat.markdown(),
            title="Bienvenido"
        ).set_language("es"),
        
        "french": GeneratedContent.create(
            content_text="# Bienvenue\n\nBienvenue sur notre plateforme.",
            template_name=TemplateName.from_user_input("welcome-template"),
            content_type=ContentType.article(),
            format=ContentFormat.markdown(),
            title="Bienvenue"
        ).set_language("fr")
    }


# ============================================================================
# Invalid/Edge Case Fixtures
# ============================================================================

@pytest.fixture
def invalid_templates():
    """Invalid template configurations for negative testing."""
    return {
        "empty_yaml": {
            "name": "empty-template",
            "yaml_content": "",
            "error": "YAML content cannot be empty"
        },
        "invalid_yaml": {
            "name": "invalid-yaml-template",
            "yaml_content": "invalid: yaml: content: [",
            "error": "Invalid YAML syntax"
        },
        "missing_metadata": {
            "name": "missing-metadata-template",
            "yaml_content": "steps:\n  test:\n    name: Test",
            "error": "Missing required metadata section"
        },
        "invalid_step_type": {
            "name": "invalid-step-template",
            "yaml_content": """metadata:
  name: Invalid Template
steps:
  test:
    name: Test Step
    type: invalid_type
    prompt_template: Test prompt""",
            "error": "Invalid step type"
        }
    }

@pytest.fixture
def edge_case_content():
    """Edge case content for boundary testing."""
    return {
        "empty_content": "",
        "very_long_content": "x" * 10000,
        "unicode_content": "🚀 Test with émojis and spëcial chars 中文",
        "markdown_with_code": """# Code Example
        
```python
def hello():
    print("Hello, World!")
```

This is code.""",
        "html_content": "<h1>HTML Content</h1><p>This contains <strong>HTML</strong> tags.</p>",
        "json_content": '{"title": "JSON Content", "data": [1, 2, 3]}',
        "mixed_formats": "# Markdown\n\n<p>HTML</p>\n\n```json\n{\"key\": \"value\"}\n```"
    }


# ============================================================================
# Factory Fixtures
# ============================================================================

@pytest.fixture
def content_factory():
    """Factory for creating content entities with custom parameters."""
    class ContentFactory:
        @staticmethod
        def create_template(
            content_type: str = "article",
            complexity: str = "simple",
            **kwargs
        ) -> Template:
            """Create template with specified characteristics."""
            if complexity == "simple":
                yaml_content = f"""metadata:
  name: "Simple {content_type.title()} Template"
  description: "Basic template for {content_type}"

defaults:
  model: "gpt-4o-mini"

inputs:
  topic:
    type: text
    label: "Topic"
    required: true

steps:
  generate:
    name: "Generate Content"
    type: llm_generate
    prompt_template: "Write a {content_type} about {{{{ inputs.topic }}}}"
    model_preference: ["{{{{ defaults.model }}}}"]
"""
            else:  # complex
                yaml_content = f"""metadata:
  name: "Advanced {content_type.title()} Template"
  description: "Advanced template with multiple steps"

defaults:
  model: "gpt-4o-mini"
  temperature: 0.7

inputs:
  topic:
    type: text
    label: "Topic"
    required: true
  style:
    type: choice
    label: "Style"
    options:
      - label: "Formal"
        value: "formal"
      - label: "Casual"
        value: "casual"

steps:
  outline:
    name: "Create Outline"
    type: llm_generate
    prompt_template: "Create outline for {content_type} about {{{{ inputs.topic }}}}"
  
  content:
    name: "Generate Content"
    type: llm_generate
    depends_on: ["outline"]
    prompt_template: "Write {content_type} based on outline: {{{{ steps.outline }}}}"
  
  review:
    name: "Review Content"
    type: llm_generate
    depends_on: ["content"]
    prompt_template: "Review and improve: {{{{ steps.content }}}}"
"""
            
            return Template.create(
                name=TemplateName.from_user_input(f"{content_type}-{complexity}-template"),
                content_type=getattr(ContentType, content_type)(),
                yaml_content=yaml_content,
                **kwargs
            )
        
        @staticmethod
        def create_style_primer(
            style_type: str = "professional",
            **kwargs
        ) -> StylePrimer:
            """Create style primer with specified characteristics."""
            style_configs = {
                "professional": {
                    "tone": "professional",
                    "voice": "third_person",
                    "writing_style": "formal",
                    "guidelines": ["Use formal language", "Be concise and clear"]
                },
                "casual": {
                    "tone": "casual",
                    "voice": "second_person", 
                    "writing_style": "conversational",
                    "guidelines": ["Use contractions", "Be friendly and approachable"]
                },
                "academic": {
                    "tone": "formal",
                    "voice": "third_person",
                    "writing_style": "academic",
                    "guidelines": ["Support with evidence", "Use precise terminology"]
                }
            }
            
            config = style_configs.get(style_type, style_configs["professional"])
            
            primer = StylePrimer.create(
                name=StyleName.from_user_input(f"{style_type}-style"),
                description=f"{style_type.title()} writing style",
                **config,
                **kwargs
            )
            
            for guideline in config["guidelines"]:
                primer = primer.add_guideline(guideline)
            
            return primer
    
    return ContentFactory()


# ============================================================================
# Valid/Invalid Entity Collections
# ============================================================================

@pytest.fixture
def valid_template(template_fixture):
    """Valid template for positive testing."""
    return template_fixture

@pytest.fixture
def invalid_template():
    """Invalid template data for negative testing."""
    return {
        "missing_name": None,
        "empty_yaml": "",
        "invalid_content_type": "invalid_type",
        "missing_yaml": None
    }