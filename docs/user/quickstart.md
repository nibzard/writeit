# Quick Start Tutorial

Create your first article with WriteIt in under 10 minutes! This tutorial walks you through the complete process from setup to published article.

## 🎯 What We'll Build

By the end of this tutorial, you'll have:
- ✅ Generated a complete technical article
- ✅ Used the 4-step pipeline (angles → outline → draft → polish)  
- ✅ Experienced real-time AI streaming
- ✅ Exported a final article with complete history
- ✅ Learned basic navigation and shortcuts

## 🚀 Before We Start

Ensure WriteIt is installed and configured:
```bash
# Check installation
writeit --version
# Should show: WriteIt 0.1.0

# Verify AI providers
llm models list | head -5
# Should show available models
```

If not installed, see [Installation Guide](installation.md).

## 📝 Tutorial: Creating Your First Article

### Step 1: Choose Your Content
For this tutorial, we'll write about WebAssembly performance. Feel free to substitute your own topic!

**Topic**: Recent advances in WebAssembly performance
**Audience**: Technical professionals
**Goal**: 800-word article about WebAssembly performance improvements

### Step 2: Start the Pipeline
```bash
# Navigate to your workspace
cd ~/articles  # or your WriteIt workspace

# Start the tech article pipeline
writeit run pipelines/tech-article.yaml
```

You should see the WriteIt TUI interface:
```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 1/4: angles (outline → draft → polish remaining)      │
├────────────────────────────────────────────────────────────┤
│ Initial Inputs:                                            │
│ ┌─ Source Material ─────────────────────────────────────────┐ │
│ │ [Empty text input field - cursor here]                  │ │
│ └────────────────────────────────────────────────────────┘ │
│ ┌─ Target Audience ─────────────────────────────────────────┐ │
│ │ technical professionals                                 │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ [Tab] Next Field [Enter] Start [Ctrl+Q] Quit              │
└────────────────────────────────────────────────────────────┘
```

### Step 3: Input Your Source Material
Type or paste this source material (or use your own):

```
Recent advances in WebAssembly (WASM) are enabling new possibilities for 
running complex applications in browsers and on servers. Major companies like 
Google, Mozilla, and Microsoft are investing heavily in WASM toolchains. 

Performance benchmarks show 90%+ native speed in many cases, with new 
features like SIMD instructions, multi-threading, and garbage collection 
making WASM suitable for CPU-intensive applications like image processing, 
scientific computing, and even full desktop applications running in browsers.

The ecosystem is maturing rapidly with frameworks like Blazor, Yew, and 
AssemblyScript making WASM development more accessible to mainstream developers.
```

**Navigation Tips**:
- `Tab` - Move between input fields
- `Enter` - Start pipeline execution
- `Ctrl+Q` - Quit WriteIt

Press `Tab` to move to Target Audience (already filled), then `Enter` to start!

### Step 4: Angles Generation
Watch as WriteIt generates multiple article angles:

```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 1/4: angles (outline → draft → polish remaining)      │
├────────────────────────────────────────────────────────────┤
│ Models: gpt-4o, claude-sonnet-4              [⚡ Streaming] │
│ ┌─ Response 1: gpt-4o ───────────────────────────────────────┐ │
│ │ # Three Article Angles for WebAssembly Performance     │ │
│ │                                                         │ │
│ │ ## 1. The 90% Performance Promise                      │ │
│ │ Focus on benchmark results showing near-native speed   │ │
│ │ and what this means for web application architecture.  │ │
│ │                                                         │ │
│ │ ## 2. Beyond the Browser: Server-Side WASM           │ │
│ │ Explore how WASM is expanding beyond web browsers...   │ │
│ │ [content continues streaming...]                       │ │
│ └────────────────────────────────────────────────────────┘ │
```

You'll see responses from both models streaming in real-time. This typically takes 30-60 seconds.

### Step 5: Select Your Angle
After both responses complete:

```
┌─ Response 1: gpt-4o ───────────────────────────────────────┐ │
│ ## 1. The 90% Performance Promise                          │ │
│ ## 2. Beyond the Browser: Server-Side WASM               │ │
│ ## 3. Developer Experience Revolution                      │ │
└────────────────────────────────────────────────────────┘ │
┌─ Response 2: claude-sonnet-4 ──────────────────────────────┐ │
│ ## A. Breaking Performance Barriers                        │ │
│ ## B. The New Runtime Revolution                          │ │
│ ## C. From Browsers to Cloud: WASM Everywhere            │ │
└────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ Your feedback for next step:                              │ │
│ ┌─ Comments ──────────────────────────────────────────────┐ │
│ │ Focus on the performance story with specific benchmarks │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ [1] Select Response 1 [2] Select Response 2 [M] Merge     │
│ [R]egenerate [F]ork [S]ave [Q]uit                         │
└────────────────────────────────────────────────────────────┘
```

**Selection Options**:
- `1` - Select the first response (gpt-4o)
- `2` - Select the second response (claude-sonnet-4)  
- `M` - Merge parts from both responses
- `R` - Regenerate both responses
- `F` - Create a branch to explore alternatives

For this tutorial, press `1` to select the first response, then `Enter`.

### Step 6: Outline Generation
WriteIt now creates a detailed outline:

```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 2/4: outline (draft → polish remaining)               │
├────────────────────────────────────────────────────────────┤
│ Input from previous step:                                  │
│ ┌─ Selected Angle ────────────────────────────────────────┐ │
│ │ ## 1. The 90% Performance Promise                       │ │
│ │ Focus on benchmark results showing near-native speed... │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ Models: gpt-4o                              [⚡ Streaming] │
│ ┌─ Response 1 ─────────────────────────────────────────────┐ │
│ │ # Outline: The WebAssembly Performance Promise         │ │
│ │                                                         │ │
│ │ ## Hook/Opening                                         │ │
│ │ - Recent Firefox demo: AAA game at 60fps in browser   │ │
│ │ - 90% native performance claim: fact or marketing?     │ │
│ │                                                         │ │
│ │ ## Section 1: Benchmark Deep Dive                      │ │
│ │ - Real-world performance comparisons                   │ │
│ │ - CPU-intensive tasks: image processing, crypto       │ │
│ │ - Memory efficiency improvements                       │ │
│ │ [outline continues...]                                  │ │
│ └────────────────────────────────────────────────────────┘ │
```

The outline incorporates your feedback about focusing on performance with specific benchmarks.

**Review the outline** - it should include:
- Strong hook/opening
- 3-5 main sections
- Specific details and examples
- Clear conclusion with takeaways

Press `A` to accept the outline, or `C` to add more feedback.

### Step 7: Draft Generation
Now WriteIt writes the full first draft:

```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 3/4: draft (polish remaining)                         │
├────────────────────────────────────────────────────────────┤
│ Models: gpt-4o, claude-sonnet-4              [⚡ Streaming] │
│ ┌─ Response 1: gpt-4o ───────────────────────────────────────┐ │
│ │ # The WebAssembly Performance Promise: Fact or Fiction? │ │
│ │                                                         │ │
│ │ When Mozilla engineers first demonstrated a AAA game   │ │
│ │ running at smooth 60fps directly in Firefox, without   │ │
│ │ plugins or downloads, the web development community    │ │
│ │ took notice. The technology behind this demo—          │ │
│ │ WebAssembly—promises near-native performance for web   │ │
│ │ applications. But can it really deliver on the bold    │ │
│ │ claim of 90% native speed?                             │ │
│ │                                                         │ │
│ │ [article continues streaming in real-time...]          │ │
│ └────────────────────────────────────────────────────────┘ │
```

This is typically the longest step (2-4 minutes) as the AI writes the complete article. You'll see the full article develop paragraph by paragraph.

**What to expect**:
- Complete article structure following the outline
- Technical details and specific examples
- Professional writing style
- Smooth transitions between sections
- Strong conclusion with actionable insights

Select your preferred draft and proceed to the final step.

### Step 8: Polish and Finalize
The final step polishes the article:

```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 4/4: polish (final step)                              │
├────────────────────────────────────────────────────────────┤
│ Models: gpt-4o-mini                         [⚡ Streaming] │
│ ┌─ Response 1 ─────────────────────────────────────────────┐ │
│ │ # The WebAssembly Performance Promise: Separating      │ │
│ │   Fact from Fiction                                     │ │
│ │                                                         │ │
│ │ When Mozilla engineers demonstrated a AAA game running │ │
│ │ at 60fps directly in Firefox—no plugins, no downloads, │ │
│ │ no compromises—they weren't just showing off cool      │ │
│ │ technology. They were proving that WebAssembly could   │ │
│ │ deliver on its ambitious promise: near-native          │ │
│ │ performance for web applications.                       │ │
│ │                                                         │ │
│ │ [polished article continues...]                        │ │
│ └────────────────────────────────────────────────────────┘ │
```

The polish step improves:
- **Clarity** - Clearer explanations and smoother flow
- **Style** - Consistent voice and tone
- **Grammar** - Perfect grammar and punctuation
- **Transitions** - Better connections between ideas
- **Impact** - Stronger opening and conclusion

### Step 9: Save Your Article
Once polishing is complete:

```
┌─ Pipeline: tech-article.yaml ──────────────────────────────┐
│ Step 4/4: polish (COMPLETED) 🎉                           │
├────────────────────────────────────────────────────────────┤
│ Your article is ready!                                     │ │
│                                                            │ │
│ Final word count: 847 words                               │ │
│ Total cost: $0.23                                         │ │
│ Processing time: 4m 32s                                   │ │
│                                                            │ │
│ [S]ave Article [E]xport [N]ew Pipeline [Q]uit             │
└────────────────────────────────────────────────────────────┘
```

Press `S` to save your article:

```
┌─ Save Article ─────────────────────────────────────────────┐
│ Output Format: [YAML] [JSON] [Markdown]                   │
│ Include History: [✓] Complete pipeline history            │
│ File Name: webassembly-performance-promise.yaml           │
│                                                            │
│ [Enter] Save [Tab] Change Options [Esc] Cancel            │
└────────────────────────────────────────────────────────────┘
```

Press `Enter` to save with default options.

## 🎉 Congratulations!

You've successfully created your first article with WriteIt! The saved file includes:

- **Final polished article** (ready to publish)
- **Complete pipeline history** (all responses and selections)
- **Cost and timing information**
- **Your feedback at each step**

## 🔍 What You've Learned

### Core Concepts
- **4-step pipeline**: angles → outline → draft → polish
- **Human-in-the-loop**: You guide the AI at each step
- **Multiple models**: Different AI providers for different strengths
- **Real-time streaming**: See content generated live
- **Complete history**: Every decision and response saved

### TUI Navigation
- `Tab` - Navigate between fields/options
- `Enter` - Confirm selection or action
- `1`, `2`, etc. - Select numbered options
- `A` - Accept current response
- `R` - Regenerate responses
- `S` - Save/export
- `Ctrl+Q` - Quit

### Key Features
- **Branching** (`F`) - Explore alternative directions
- **Rewind** (`B`) - Go back to previous steps
- **Merging** (`M`) - Combine multiple AI responses
- **Feedback** - Guide AI behavior with comments

## 🚀 Next Steps

### Try Different Pipelines
```bash
# Blog post pipeline (more casual tone)
writeit run pipelines/blog-post.yaml

# Research summary pipeline (academic style)
writeit run pipelines/research-summary.yaml
```

### Explore Advanced Features
- **[Pipeline Configuration](pipeline-config.md)** - Create custom workflows
- **[Advanced Features](advanced-features.md)** - Branching, styling, automation
- **[Style Customization](../examples/tui-customization.md)** - Personalize your writing voice

### View Your Article
```bash
# Open your saved article
cat ~/articles/runs/webassembly-performance-promise.yaml

# Or view just the final content
writeit show webassembly-performance-promise.yaml --content-only
```

## 💡 Pro Tips

### Speed Up Your Workflow
1. **Use keyboard shortcuts** - Much faster than mouse/trackpad
2. **Prepare source material** - Have your research ready beforehand
3. **Write clear feedback** - Specific guidance gets better results
4. **Save regularly** - Use `S` to save progress at any step

### Get Better Results
1. **Be specific in feedback** - "Add more technical details" vs "Make it better"
2. **Choose the right pipeline** - Tech article vs blog post vs academic
3. **Review before accepting** - Take time to read AI responses
4. **Experiment with branching** - Try different angles and compare

### Manage Your Workspace
```bash
# View recent articles
writeit list runs --recent 10

# Clean up old artifacts  
writeit cleanup --older-than 30d

# Backup important articles
writeit export ~/articles/runs/important-article.yaml ~/backup/
```

## 🆘 Troubleshooting

### Common Issues During Tutorial

**"Connection failed" or "Model not found"**
```bash
# Check your AI provider setup
llm models list
llm keys list

# Reset provider keys if needed
llm keys set openai
```

**TUI doesn't display correctly**
```bash
# Check terminal compatibility
echo $TERM
tput colors

# Try with basic colors
writeit --no-color run pipelines/tech-article.yaml
```

**Article seems low quality**
- Try providing more specific feedback
- Use a different AI model (switch providers)
- Add more detailed source material
- Try the regenerate option (`R`)

**Want to start over?**
- Press `Ctrl+Q` to quit
- Run the same command again
- Your previous work is automatically saved

## 📚 Additional Resources

### Learn More
- **[Installation Guide](installation.md)** - Detailed setup instructions
- **[Pipeline Configuration](pipeline-config.md)** - Create custom workflows
- **[API Documentation](../api/rest-api.md)** - Programmatic access

### Get Help
- **Built-in help**: `writeit --help`
- **Community**: [Discord](https://discord.gg/writeIt)
- **Issues**: [GitHub](https://github.com/writeIt/writeIt/issues)

---

**Ready to create more content?** Try different topics, experiment with branching, or create your own custom pipeline! 🚀