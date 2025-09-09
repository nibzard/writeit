# Pipeline Examples

WriteIt comes with several pre-built pipeline configurations for different content types. This guide shows you how to use, customize, and create new pipelines.

## 📚 Built-in Pipelines

### Tech Article Pipeline
**File**: `pipelines/tech-article.yaml`
**Best for**: Technical blog posts, engineering articles, developer content

```yaml
metadata:
  name: "tech-article-pipeline"
  description: "Technical article generation with code examples and benchmarks"
  version: "1.0"

defaults:
  temperature: 0.7
  max_tokens: 2000
  style_primer: "styles/tech-journalist.txt"

inputs:
  - name: "source_material"
    type: "text"
    required: true
    description: "Technical information, research, or topic overview"
  - name: "target_audience"
    type: "text"
    default: "technical professionals"
    description: "Who will read this article"
  - name: "technical_depth"
    type: "select"
    options: ["beginner", "intermediate", "advanced"]
    default: "intermediate"

steps:
  - name: "angles"
    description: "Generate multiple technical article angles"
    models: ["gpt-4o", "claude-sonnet-4"]
    responses_per_model: 2
    template: |
      Based on this technical content: {source_material}
      Target audience: {target_audience} ({technical_depth} level)
      Style: {style_primer}
      
      Generate 3 distinct article angles that would engage {target_audience}.
      Focus on: practical applications, real-world examples, actionable insights.
      Each angle should include specific technical details and code examples where relevant.
      
      Previous feedback: {user_feedback}
  
  - name: "outline"
    description: "Create detailed technical outline"
    models: ["gpt-4o"]
    template: |
      Selected angle: {angles_output}
      Technical depth: {technical_depth}
      Style: {style_primer}
      
      Create a comprehensive outline with:
      - Compelling hook (real-world example or surprising statistic)
      - 4-5 main sections with technical depth appropriate for {technical_depth} readers
      - Code examples and implementation details where relevant
      - Performance considerations and best practices
      - Conclusion with next steps and additional resources
      
      User guidance: {user_feedback}
      
  - name: "draft"
    description: "Write complete technical article"
    models: ["gpt-4o", "claude-sonnet-4"]
    responses_per_model: 1
    params:
      max_tokens: 3500
    template: |
      Outline: {outline_output}
      Technical level: {technical_depth}
      Style: {style_primer}
      
      Write a complete technical article following this outline.
      Include:
      - Working code examples with explanations
      - Performance benchmarks where relevant
      - Best practices and common pitfalls
      - Links to documentation and resources
      - Clear explanations that match the {technical_depth} level
      
      User direction: {user_feedback}

  - name: "polish"
    description: "Technical review and refinement"
    models: ["gpt-4o-mini"]
    template: |
      Technical article: {draft_output}
      Target audience: {target_audience} ({technical_depth})
      Style: {style_primer}
      
      Polish this technical article for:
      - Technical accuracy and clarity
      - Code example correctness and formatting
      - Appropriate complexity for {technical_depth} readers
      - Strong transitions and logical flow
      - Professional technical writing style
      - SEO-friendly structure with clear headings
      
      Specific requests: {user_feedback}
```

**Usage Example**:
```bash
writeit run pipelines/tech-article.yaml
# Input: "WebAssembly performance improvements in 2024"
# Output: 1200-word technical article with benchmarks and code examples
```

### Blog Post Pipeline
**File**: `pipelines/blog-post.yaml`
**Best for**: Personal blogs, company blogs, casual content

```yaml
metadata:
  name: "blog-post-pipeline"
  description: "Engaging blog post generation with conversational tone"
  version: "1.0"

defaults:
  temperature: 0.8
  max_tokens: 1500
  style_primer: "styles/conversational.txt"

inputs:
  - name: "topic"
    type: "text"
    required: true
    description: "Blog post topic or theme"
  - name: "target_audience"
    type: "text"
    default: "general readers"
    description: "Your blog audience"
  - name: "post_type"
    type: "select"
    options: ["how-to", "opinion", "news", "story", "list"]
    default: "how-to"
  - name: "tone"
    type: "select"
    options: ["professional", "casual", "friendly", "humorous"]
    default: "friendly"

steps:
  - name: "angles"
    description: "Generate engaging blog post angles"
    models: ["gpt-4o-mini", "claude-haiku"]
    responses_per_model: 3
    template: |
      Topic: {topic}
      Audience: {target_audience}
      Post type: {post_type}
      Tone: {tone}
      Style: {style_primer}
      
      Generate 3 engaging blog post angles for this {post_type} post.
      Make them:
      - Attention-grabbing and clickable
      - Valuable to {target_audience}
      - Suitable for a {tone} tone
      - Structured for easy reading
      
      Previous feedback: {user_feedback}
  
  - name: "outline"
    description: "Create blog post structure"
    models: ["gpt-4o-mini"]
    template: |
      Selected angle: {angles_output}
      Post type: {post_type}
      Tone: {tone}
      Style: {style_primer}
      
      Create a blog post outline with:
      - Compelling introduction that hooks readers
      - Clear main points (3-7 sections for {post_type})
      - Practical examples and actionable advice
      - Engaging conclusion with call-to-action
      - SEO-friendly structure
      
      Keep the {tone} tone throughout.
      User guidance: {user_feedback}
      
  - name: "draft"
    description: "Write engaging blog post"
    models: ["gpt-4o", "claude-sonnet-4"]
    template: |
      Outline: {outline_output}
      Tone: {tone}
      Audience: {target_audience}
      Style: {style_primer}
      
      Write a complete blog post that:
      - Engages readers from the first sentence
      - Uses a {tone}, conversational writing style
      - Includes personal anecdotes or examples where appropriate
      - Provides real value to {target_audience}
      - Has clear subheadings and bullet points for scannability
      - Ends with an engaging conclusion and call-to-action
      
      User direction: {user_feedback}

  - name: "polish"
    description: "Blog post optimization"
    models: ["gpt-4o-mini"]
    template: |
      Blog post: {draft_output}
      Target tone: {tone}
      Style: {style_primer}
      
      Polish this blog post for:
      - Engaging, {tone} voice throughout
      - Clear, scannable formatting
      - Strong hook and compelling conclusion
      - Natural keyword integration
      - Social media shareability
      - Grammatical perfection
      
      Specific requests: {user_feedback}
```

### Research Summary Pipeline
**File**: `pipelines/research-summary.yaml`
**Best for**: Academic papers, research reports, white papers

```yaml
metadata:
  name: "research-summary-pipeline"
  description: "Academic research summary with citations and analysis"
  version: "1.0"

defaults:
  temperature: 0.3
  max_tokens: 2500
  style_primer: "styles/academic.txt"

inputs:
  - name: "research_papers"
    type: "text"
    required: true
    description: "Research papers, studies, or academic sources to summarize"
  - name: "research_focus"
    type: "text"
    required: true
    description: "Specific aspect or question to focus on"
  - name: "target_audience"
    type: "select"
    options: ["academics", "industry", "general-educated"]
    default: "academics"
  - name: "citation_style"
    type: "select"
    options: ["APA", "MLA", "Chicago", "IEEE"]
    default: "APA"

steps:
  - name: "angles"
    description: "Analyze research focus areas"
    models: ["gpt-4o", "claude-sonnet-4"]
    responses_per_model: 2
    template: |
      Research material: {research_papers}
      Focus area: {research_focus}
      Target audience: {target_audience}
      Citation style: {citation_style}
      Style: {style_primer}
      
      Analyze the research and identify 3 key analytical frameworks for {research_focus}.
      Each framework should:
      - Address a specific aspect of {research_focus}
      - Be appropriate for {target_audience}
      - Allow for systematic analysis of the research
      - Support evidence-based conclusions
      
      Previous feedback: {user_feedback}
  
  - name: "outline"
    description: "Create research summary structure"
    models: ["claude-sonnet-4"]
    template: |
      Selected framework: {angles_output}
      Research focus: {research_focus}
      Citation style: {citation_style}
      Style: {style_primer}
      
      Create a structured research summary outline:
      - Executive summary/abstract
      - Introduction with research question
      - Methodology or analytical approach
      - Key findings organized by theme
      - Analysis and interpretation
      - Limitations and future research
      - Conclusion and implications
      - References section ({citation_style} format)
      
      Ensure academic rigor appropriate for {target_audience}.
      User guidance: {user_feedback}
      
  - name: "draft"
    description: "Write comprehensive research summary"
    models: ["gpt-4o", "claude-sonnet-4"]
    params:
      max_tokens: 4000
    template: |
      Outline: {outline_output}
      Research material: {research_papers}
      Citation style: {citation_style}
      Style: {style_primer}
      
      Write a comprehensive research summary that:
      - Maintains academic objectivity and rigor
      - Properly cites sources in {citation_style} format
      - Synthesizes findings across multiple sources
      - Identifies gaps and contradictions in research
      - Provides balanced analysis and interpretation
      - Uses appropriate academic terminology for {target_audience}
      - Includes methodological considerations
      
      User direction: {user_feedback}

  - name: "polish"
    description: "Academic review and citation check"
    models: ["gpt-4o"]
    template: |
      Research summary: {draft_output}
      Citation style: {citation_style}
      Target audience: {target_audience}
      Style: {style_primer}
      
      Polish this research summary for:
      - Academic writing standards and objectivity
      - Proper {citation_style} citation formatting
      - Logical argument structure and evidence flow
      - Appropriate terminology for {target_audience}
      - Balanced presentation of multiple perspectives
      - Clear methodology and limitation discussions
      - Professional academic presentation
      
      Specific requests: {user_feedback}
```

## 🎨 Custom Pipeline Creation

### Creating Your Own Pipeline

1. **Start with a Template**:
```bash
# Copy existing pipeline
cp pipelines/tech-article.yaml pipelines/my-custom-pipeline.yaml
```

2. **Customize Metadata**:
```yaml
metadata:
  name: "my-custom-pipeline"
  description: "Custom pipeline for my specific needs"
  version: "1.0"
  author: "Your Name"
  created: "2025-01-15"
```

3. **Define Your Inputs**:
```yaml
inputs:
  - name: "primary_input"
    type: "text"
    required: true
    description: "Main content input"
    placeholder: "Enter your content here..."
  
  - name: "style_preference"
    type: "select"
    options: ["formal", "casual", "technical"]
    default: "formal"
    description: "Writing style preference"
  
  - name: "word_count_target"
    type: "number"
    min: 500
    max: 5000
    default: 1000
    description: "Target word count"
```

4. **Customize Steps**:
```yaml
steps:
  - name: "analysis"
    description: "Analyze input content"
    models: ["gpt-4o"]
    template: |
      Content: {primary_input}
      Style: {style_preference}
      Target length: {word_count_target} words
      
      Analyze this content and identify:
      1. Key themes and topics
      2. Target audience implications
      3. Potential angles for {style_preference} treatment
      4. Structure recommendations for {word_count_target}-word piece
      
      User feedback: {user_feedback}
```

### Industry-Specific Examples

#### Marketing Copy Pipeline
```yaml
# pipelines/marketing-copy.yaml
metadata:
  name: "marketing-copy-pipeline"
  description: "High-converting marketing copy generation"

inputs:
  - name: "product_service"
    type: "text"
    required: true
  - name: "target_market"
    type: "text" 
    required: true
  - name: "copy_type"
    type: "select"
    options: ["landing-page", "email", "ad-copy", "social-media"]
  - name: "brand_voice"
    type: "select"
    options: ["professional", "playful", "authoritative", "friendly"]

steps:
  - name: "market_research"
    description: "Analyze target market and positioning"
    # ... market analysis templates
    
  - name: "value_proposition"  
    description: "Craft compelling value propositions"
    # ... value prop templates
    
  - name: "copy_creation"
    description: "Write persuasive copy"
    # ... copy writing templates
    
  - name: "optimization"
    description: "Optimize for conversion"
    # ... A/B testing suggestions
```

#### News Article Pipeline
```yaml
# pipelines/news-article.yaml
metadata:
  name: "news-article-pipeline" 
  description: "Objective news reporting with fact-checking focus"

inputs:
  - name: "news_sources"
    type: "text"
    required: true
    description: "Primary and secondary sources"
  - name: "story_angle"
    type: "text"
    description: "Specific angle or focus"
  - name: "urgency"
    type: "select"
    options: ["breaking", "developing", "feature", "analysis"]

steps:
  - name: "fact_verification"
    description: "Verify facts and sources"
    models: ["gpt-4o"]
    template: |
      Sources: {news_sources}
      Story type: {urgency}
      
      Verify and cross-reference the key facts:
      1. Primary claims and statements
      2. Source credibility and bias assessment  
      3. Missing information or context needed
      4. Timeline verification
      5. Quote accuracy and context
      
  - name: "lead_generation"
    description: "Create compelling news leads"
    # ... journalism lead templates
    
  - name: "article_structure"
    description: "Structure using inverted pyramid"
    # ... news structure templates
    
  - name: "editorial_review"
    description: "Editorial standards review"
    # ... fact-checking and style review
```

## 🔧 Advanced Pipeline Features

### Conditional Steps
```yaml
steps:
  - name: "content_analysis"
    description: "Analyze content type"
    models: ["gpt-4o-mini"]
    template: |
      Content: {input_content}
      
      Determine if this content is:
      - Technical (needs code examples)
      - Business (needs case studies) 
      - Creative (needs storytelling)
      
      Output: technical|business|creative
      
  - name: "technical_draft"
    description: "Technical content creation"
    condition: "content_analysis.output == 'technical'"
    models: ["gpt-4o"]
    template: |
      # Technical-specific template
      
  - name: "business_draft"
    description: "Business content creation"  
    condition: "content_analysis.output == 'business'"
    models: ["claude-sonnet-4"]
    template: |
      # Business-specific template
      
  - name: "creative_draft"
    description: "Creative content creation"
    condition: "content_analysis.output == 'creative'"
    models: ["gpt-4o"]
    template: |
      # Creative-specific template
```

### Multi-Language Support
```yaml
inputs:
  - name: "target_language"
    type: "select"
    options: ["english", "spanish", "french", "german"]
    default: "english"
  - name: "localization_notes"
    type: "text"
    description: "Cultural adaptation notes"

steps:
  - name: "cultural_adaptation"
    description: "Adapt content for target culture"
    template: |
      Content: {draft_output}
      Target language: {target_language}
      Cultural notes: {localization_notes}
      
      Adapt this content for {target_language} readers:
      1. Cultural references and examples
      2. Idiomatic expressions
      3. Local business practices
      4. Regional preferences
      
  - name: "translation_review"
    description: "Review translation quality"
    models: ["gpt-4o"]
    template: |
      Original: {draft_output}
      Translated: {cultural_adaptation_output}
      Language: {target_language}
      
      Review translation for:
      - Accuracy and fluency
      - Cultural appropriateness
      - Technical term consistency
      - Natural flow in target language
```

### Pipeline Inheritance
```yaml
# pipelines/base-article.yaml
metadata:
  name: "base-article-pipeline"
  type: "base"

defaults:
  temperature: 0.7
  style_primer: "styles/default.txt"

steps:
  - name: "angles"
    # Base angle generation
  - name: "outline"  
    # Base outline creation

---
# pipelines/tech-article.yaml
metadata:
  name: "tech-article-pipeline"
  extends: "base-article-pipeline"
  
# Override specific steps
steps:
  - name: "angles"
    models: ["gpt-4o", "claude-sonnet-4"]  # Override base
    template: |
      # Tech-specific angle template
      
  - name: "technical_review"  # Add new step
    description: "Technical accuracy review"
    models: ["gpt-4o"]
    template: |
      # Technical review template
```

## 📊 Pipeline Testing

### Test Configuration
```yaml
# tests/pipeline-test.yaml
test_pipelines:
  - pipeline: "tech-article.yaml"
    test_cases:
      - name: "webassembly_performance"
        inputs:
          source_material: "WebAssembly benchmarks show 90% native performance..."
          target_audience: "technical professionals"
          technical_depth: "intermediate"
        expected_outputs:
          word_count: [800, 1200]
          technical_terms: ["WebAssembly", "performance", "benchmarks"]
          code_examples: true
          
  - pipeline: "blog-post.yaml"
    test_cases:
      - name: "productivity_tips"
        inputs:
          topic: "Morning productivity routines"
          target_audience: "working professionals"
          tone: "friendly"
        expected_outputs:
          word_count: [600, 1000]
          sections: [3, 7]
          call_to_action: true
```

### Running Pipeline Tests
```bash
# Test specific pipeline
writeit test pipelines/tech-article.yaml

# Test all pipelines
writeit test-all

# Generate test report
writeit test-report --format html --output test-results.html
```

This comprehensive guide provides everything you need to use existing pipelines effectively and create custom ones tailored to your specific content needs.