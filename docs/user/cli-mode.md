# CLI Mode Guide

WriteIt's CLI mode provides a streamlined, automation-friendly interface for pipeline execution without the TUI overhead. Perfect for scripts, CI/CD pipelines, and environments where you prefer simple text prompts.

## 🚀 Quick Start

```bash
# Compare the two execution modes:

# TUI Mode (default) - Interactive visual interface
writeit run tech-article

# CLI Mode - Simple text prompts  
writeit run tech-article --cli
```

## 🎯 When to Use CLI Mode

### ✅ Perfect For:
- **Automation & Scripting**: Batch content generation
- **CI/CD Pipelines**: Automated documentation generation
- **Remote Environments**: SSH sessions, containers, terminals
- **Simple Workflows**: When you prefer text prompts
- **Production Systems**: Reliable, non-interactive execution
- **Resource Constraints**: Lighter than full TUI

### 🔄 TUI Mode Better For:
- Interactive content creation
- Exploring different content branches
- Real-time streaming visualization
- Learning WriteIt's capabilities
- Complex pipeline debugging

## 📋 Input Types & User Experience

CLI mode handles all the same input types as TUI mode with simple prompts:

### Text Input
```bash
Topic: Python Performance Optimization  # Simple text entry
```

### Choice/Select Options
```bash
Target Audience:
  1. beginners - New to programming
  2. intermediate - Some experience
  3. advanced - Expert developers
Select option (number): 2
```

### Textarea (Multi-line)
```bash
Enter your source material (press Ctrl+D when finished):
Recent advances in Python performance include...
[Multiple lines of content]
[Ctrl+D to finish]
```

### Yes/No Confirmations
```bash
Execute step: Generate Outline? [y/n] (y): y
Accept this response? [y/n] (y): n
Continue despite error? [y/n] (n): y
```

## 🔧 CLI Mode Features

### Progress Indicators
```bash
⠋ Processing with LLM...
```

### Rich Response Display
```bash
✅ Response:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Here are 5 compelling angles for your article:                            ┃
┃                                                                            ┃
┃ 1. **Performance First**: Focus on optimization techniques                 ┃
┃ 2. **Real-World Examples**: Practical case studies                        ┃
┃ 3. **Tools & Profiling**: Systematic bottleneck identification           ┃
┃ [...]                                                                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Token Usage Tracking
```bash
✅ Pipeline Completed!

Token Usage Summary:
  Total Input Tokens: 1,247
  Total Output Tokens: 2,891  
  Total Steps: 4

Executed 4 steps:
  angles: ✅ Completed
  outline: ✅ Completed
  write: ✅ Completed
  polish: ✅ Completed
```

### Error Handling
```bash
Error executing step Generate Outline: API rate limit exceeded
Continue despite error? [y/n] (n): y
Regenerate? [y/n] (y): y
```

## 🤖 Automation Examples

### Basic Scripting
```bash
#!/bin/bash
# Simple article generation script

topic="$1"
if [ -z "$topic" ]; then
  echo "Usage: $0 'Article Topic'"
  exit 1
fi

echo -e "${topic}\n2\ny\ny\ny\ny" | \
  writeit run tech-article --cli --workspace blog
```

### Batch Processing
```bash
#!/bin/bash
# Batch generate articles from a list

articles=(
  "Python Best Practices"
  "Docker Fundamentals" 
  "API Design Patterns"
  "Database Optimization"
  "Testing Strategies"
)

workspace="tech-blog"
success_count=0

for topic in "${articles[@]}"; do
  echo "Generating: $topic"
  
  if echo -e "${topic}\n2\n1\ny\ny\ny\ny" | \
     writeit run tech-article --cli --workspace "$workspace"; then
    echo "✅ Success: $topic"
    ((success_count++))
  else
    echo "❌ Failed: $topic"
  fi
  
  echo "---"
done

echo "Completed $success_count/${#articles[@]} articles"
```

### Error Handling & Retries
```bash
#!/bin/bash
# Robust generation with retries

generate_with_retry() {
  local topic="$1"
  local workspace="$2" 
  local max_attempts=3
  
  for attempt in $(seq 1 $max_attempts); do
    echo "Attempt $attempt/$max_attempts: $topic"
    
    if echo -e "${topic}\n2\ny\ny\ny\ny" | \
       writeit run tech-article --cli --workspace "$workspace" 2>/dev/null; then
      echo "✅ Success: $topic"
      return 0
    else
      echo "❌ Attempt $attempt failed: $topic"
      [ $attempt -lt $max_attempts ] && sleep 5
    fi
  done
  
  echo "🚫 Failed after $max_attempts attempts: $topic"
  return 1
}

# Usage
generate_with_retry "Advanced Python Patterns" "dev-blog"
```

## 🏭 CI/CD Integration

### GitHub Actions
```yaml
name: Generate Documentation

on:
  push:
    paths: ['docs/specs/**']
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Monday

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
      
    - name: Setup uv
      uses: astral-sh/setup-uv@v1
      
    - name: Install WriteIt
      run: uv tool install writeit[openai,anthropic]
      
    - name: Generate API Documentation  
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        WRITEIT_WORKSPACE: api-docs
      run: |
        # Generate documentation for each API version
        for version in v1 v2 v3; do
          echo -e "API $version Documentation\n2\ny\ny\ny\ny" | \
            writeit run api-docs --cli --workspace production
        done
        
    - name: Commit generated docs
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add docs/
        git commit -m "Auto-generated documentation" || exit 0
        git push
```

### Jenkins Pipeline
```groovy
pipeline {
    agent any
    
    environment {
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
        WRITEIT_WORKSPACE = 'release-notes'
    }
    
    triggers {
        // Run weekly on Sunday at 2 AM
        cron('0 2 * * 0')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'curl -LsSf https://astral.sh/uv/install.sh | sh'
                sh 'uv tool install writeit[openai,anthropic]'
            }
        }
        
        stage('Generate Release Notes') {
            steps {
                script {
                    def version = env.BUILD_NUMBER
                    
                    sh """
                        echo -e "Version ${version} Release Notes\\n1\\ny\\ny\\ny\\ny" | \\
                          writeit run release-notes --cli
                    """
                }
            }
        }
        
        stage('Publish') {
            steps {
                archiveArtifacts artifacts: '**/*.md', fingerprint: true
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'output',
                    reportFiles: '*.html',
                    reportName: 'Generated Documentation'
                ])
            }
        }
    }
    
    post {
        failure {
            emailext (
                subject: "WriteIt Documentation Generation Failed - Build ${env.BUILD_NUMBER}",
                body: "The automated documentation generation has failed. Please check the build logs.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
```

### GitLab CI
```yaml
# .gitlab-ci.yml
stages:
  - generate
  - deploy

generate-docs:
  stage: generate
  image: python:3.12-slim
  
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="/root/.cargo/bin:$PATH"
    - uv tool install writeit[openai,anthropic]
    
  script:
    - |
      # Generate documentation for different products
      products=("API" "SDK" "CLI" "Web")
      
      for product in "${products[@]}"; do
        echo "Generating docs for $product"
        echo -e "${product} Documentation\n2\ny\ny\ny\ny" | \
          writeit run product-docs --cli --workspace production
      done
      
  artifacts:
    paths:
      - docs/
    expire_in: 1 week
    
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
    WRITEIT_WORKSPACE: production-docs
    
  only:
    - main
    - develop
```

## 🔀 Interactive vs Non-Interactive

### Fully Interactive
```bash
# User provides all inputs manually
writeit run tutorial --cli
```

### Semi-Automated  
```bash
# Pre-fill some inputs, prompt for others
echo -e "Docker Basics\n1" | writeit run tutorial --cli
```

### Fully Automated
```bash
# All inputs provided via stdin
echo -e "Docker Basics\n1\ny\ny\ny\ny" | writeit run tutorial --cli
```

### Conditional Automation
```bash
#!/bin/bash
# Different behavior in CI vs local development

if [ "$CI" = "true" ]; then
    # CI: fully automated
    echo -e "Auto-generated docs\n2\ny\ny\ny" | \
      writeit run api-docs --cli --workspace production
else
    # Local: interactive for better control
    writeit run api-docs --cli --workspace development
fi
```

## 🌍 Environment Variables

CLI mode respects all the same environment variables as TUI mode:

```bash
# WriteIt configuration
export WRITEIT_HOME=/opt/writeit
export WRITEIT_WORKSPACE=production

# AI provider keys
export OPENAI_API_KEY=sk-your-key
export ANTHROPIC_API_KEY=sk-ant-your-key

# Run with environment config
writeit run tech-article --cli
```

## 🚨 Error Scenarios & Handling

### API Failures
```bash
Error executing step Generate Outline: API rate limit exceeded
Continue despite error? [y/n] (n): y
# Choose 'y' to skip this step, 'n' to abort pipeline
```

### Invalid Input
```bash
Select option (number): invalid
Please enter a number.
Select option (number): 5
Invalid selection. Please try again.
Select option (number): 2
```

### Pipeline Configuration Issues
```bash
❌ Pipeline not found: nonexistent-pipeline

Use 'writeit pipeline list' to see available pipelines
```

### Missing Dependencies
```bash
❌ CLI execution failed: No LLM model available: No API keys configured

Please configure at least one AI provider:
  llm keys set openai
  llm keys set anthropic
```

## 🔍 Debugging CLI Mode

### Verbose Output
```bash
# Enable verbose logging
writeit --verbose run tech-article --cli
```

### Dry Run Testing
```bash
# Test input collection without LLM calls
echo -e "test topic\n1\nn\nn\nn\nn" | writeit run tech-article --cli
```

### Pipeline Validation
```bash
# Validate pipeline before execution
writeit validate tech-article --detailed
writeit run tech-article --cli
```

## 📊 Performance & Resource Usage

CLI mode offers several advantages for resource-constrained environments:

- **Memory**: ~70% less memory usage than TUI mode
- **CPU**: No rendering overhead, pure text processing
- **Dependencies**: No Textual UI library required
- **Startup**: ~2x faster startup time
- **Network**: Same LLM API usage as TUI mode

## 🔄 Migration from TUI

Switching between modes is seamless - same pipeline configs, same workspaces:

```bash
# Your existing TUI command
writeit run my-pipeline

# Add --cli flag for CLI mode  
writeit run my-pipeline --cli

# All workspace and configuration options work the same
writeit run my-pipeline --cli --workspace production --global
```

## 📚 Best Practices

### 1. Input Validation
```bash
# Validate inputs before pipeline execution
if [[ -z "$TOPIC" ]]; then
  echo "Error: TOPIC environment variable required"
  exit 1
fi
```

### 2. Error Recovery
```bash
# Always handle potential failures
if ! echo -e "${topic}\n2\ny\ny\ny\ny" | writeit run article --cli; then
  echo "Pipeline failed, attempting with different model..."
  echo -e "${topic}\n2\ny\ny\ny\ny" | writeit run article-backup --cli
fi
```

### 3. Logging
```bash
# Log all operations for debugging
exec > >(tee -a pipeline.log)
exec 2>&1

echo "$(date): Starting pipeline for: $topic"
echo -e "${topic}\n2\ny\ny\ny\ny" | writeit run article --cli
echo "$(date): Pipeline completed"
```

### 4. Resource Management
```bash
# Process articles in batches to avoid rate limits
batch_size=3
count=0

for topic in "${topics[@]}"; do
  generate_article "$topic" &
  ((count++))
  
  if ((count % batch_size == 0)); then
    wait  # Wait for batch to complete
    sleep 30  # Rate limit pause
  fi
done

wait  # Wait for remaining jobs
```

---

CLI mode makes WriteIt's powerful pipeline system accessible to automation, scripting, and production environments while maintaining the same quality and capabilities as the interactive TUI mode. Choose the right mode for your use case and leverage WriteIt's flexibility! 🚀
