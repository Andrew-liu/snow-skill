---
name: snow-x-article
description: This skill should be used when writing, rewriting, researching, polishing, or packaging long-form X/Twitter articles in Markdown. It preserves the user's voice, supports research and citation management, applies a self-contained anti-AI-writing editorial pass, and produces a final X-ready long-form Markdown article. Trigger on “X长文”, “推特长文”, “写长文”, “改长文”, “重写文章”, “生成X长文”, or @command://snow-x-article.
---

# Snow X Article

Create publication-ready **X long-form articles**. Treat this as an editorial workflow, not a tweet/thread generator.

Core promise:

1. Preserve the user's voice and strongest original lines.
2. Research missing facts when needed and keep claims traceable.
3. Convert notes, outlines, or thread-like drafts into natural long-form article paragraphs.
4. Apply a self-contained anti-AI-writing pass before final delivery.
5. Produce a clean X-ready Markdown article.

## Critical Default Rules

When the user asks for a **long article / X long-form / Markdown article**:

- Do **not** write in thread style unless explicitly requested.
- Do **not** use one sentence per paragraph as the default.
- Use natural article paragraphs: target 2-5 sentences per paragraph.
- Keep short paragraphs only for emphasis, not as every line.
- Separate reader-facing正文 from author notes / research notes / publishing notes.
- Use level-2 headings (`## 01｜...`) for every reader-facing正文 section. Reserve `###` only for rare subsections or appendices when explicitly needed.
- Preserve the user's first-person voice and informal style when present.
- Avoid turning the article into a corporate report or academic paper unless explicitly requested.
- Do not expose local/private source names in reader-facing正文 unless the user explicitly asks.

Bad article layout:

```markdown
我以前以为 RAG 就是向量库。

后来发现不是。

最近我看了一些资料。

所以我改变了看法。
```

Better article layout:

```markdown
我以前以为 RAG 就是向量库，后来发现这个理解太小了。最近重新看了一些资料后，我更愿意把 RAG 理解成一种给 LLM 找上下文的方式，而不是某个固定的数据库方案。
```

## Output Location

When the user provides a target file, edit that file directly.

When no target file is provided and the workspace has an `Obsidian/02-X/` directory, create the article under:

```text
{workspace}/Obsidian/02-X/{标题}_X长文.md
```

If that path is not available, use the current workspace and report the path.

## Checkpoints

Use explicit checkpoints for complex or destructive work.

### Checkpoint 1 — Outline Approval

Stop and ask for confirmation before drafting the full article when:

- the user asks to write a new long-form article from rough notes
- the topic is broad or research-heavy
- the article structure is unclear
- the output will be longer than 1,500 Chinese characters

Skip this checkpoint only when the user explicitly asks to directly rewrite an existing file.

### Checkpoint 2 — Destructive Edit / Final Overwrite

Before overwriting an existing Markdown file:

1. Read the whole file.
2. Confirm the output path.
3. If the rewrite changes more than formatting, state that the file will be overwritten.
4. Keep a concise completion note after writing.

If the user already gave a direct command like “覆盖 / 落地到这个文件 / 重写这个文件”, treat that as approval after reading the file.

## Three-Stage Workflow

### Stage 1 — Research, Outline, Voice, Citations

1. Understand the writing project:
   - topic
   - main argument
   - audience
   - target format
   - goal: educate / explain / persuade / entertain
   - sources to use or avoid
   - writing voice

2. Build or refine an outline before rewriting:
   - hook
   - context
   - main sections
   - examples / evidence
   - conclusion
   - citation needs

3. Conduct research when needed:
   - use web search / web fetch for current facts
   - read user-provided local files when relevant
   - distinguish verified facts from personal interpretation
   - avoid citing private/local sources in the reader-facing article unless the user asks

4. Preserve author voice:
   - keep first-person observations
   - keep useful lived details
   - keep rough-but-real phrasing when it improves authenticity
   - improve clarity without replacing the user’s personality

5. Manage citations:
   - use light citations for X long-form
   - add a short `参考来源` section when the article cites papers, web articles, reports, or factual claims that need traceability
   - do not overload the article with academic-style inline citations unless requested

### Stage 2 — Anti-AI-Writing Editorial Pass

Use this self-contained standard before final delivery.

Mandatory checks:

1. Remove AI-like filler:
   - “值得注意的是” when unnecessary
   - “在当今快速变化的时代”
   - “让我们深入探讨”
   - generic opening politeness

2. Break formulaic structures:
   - forced three-part lists
   - repeated “不是 X，而是 Y” patterns
   - mechanical setup / reveal structures
   - repeated “从 X 到 Y” framing when X/Y do not form a meaningful range

3. Remove marketing / corporate tone:
   - 赋能
   - 至关重要
   - 深刻变革
   - 不断演变的格局
   - 里程碑式
   - 生态、闭环、抓手 when used as empty jargon

4. Avoid dash spam:
   - avoid `——` and overused `—`
   - use commas, colons, periods, or paragraph breaks instead

5. Improve paragraph rhythm:
   - merge isolated one-line sentences into real paragraphs
   - keep 1-line paragraphs only for deliberate emphasis
   - mix short, medium, and long sentences
   - use section headings to create structure, not excessive blank lines

6. Preserve human voice:
   - keep concrete details over generic summary
   - keep uncertainty when the author is genuinely unsure
   - keep first-person phrasing when it carries personality
   - prefer authentic roughness over polished corporate prose

7. Score the article after revision:

| Dimension | Meaning | /10 |
|---|---|---|
| Directness | says the point without ceremonial framing | |
| Rhythm | natural paragraph and sentence variation | |
| Trust | avoids over-explaining and fake certainty | |
| Human voice | sounds like a real person, not a generated essay | |
| Concision | removes filler while keeping substance | |

Gate:

- ≥45/50: ready for final review
- 40-44/50: acceptable but polish once if easy
- <40/50: revise before finalizing

### Stage 3 — Final Review and X-Ready Markdown

Perform a final editorial review:

1. Structure:
   - hook works
   - sections are ordered logically
   - no work-in-progress notes are mixed into正文
   - publishing notes are separated at the end

2. Readability:
   - paragraphs read like an article, not a thread
   - no excessive blank-line stacking
   - no long walls of text
   - section titles are useful, not decorative

3. Facts:
   - key claims are sourced or framed as opinion
   - uncertainties are marked
   - private/local/internal sources are not exposed unless user asked

4. Anti-AI-writing:
   - run Stage 2 checks again after the final edit
   - ensure titles, captions, and notes do not add AI-like phrasing

5. Final file structure:

```markdown
# 标题

> 用途 / 主题 / 日期 / 版本（可选）

## X 长文正文

## 01｜...

正文自然段。

## 02｜...

正文自然段。

---

## 参考来源（可选）

1. ...

## 标题备选（可选）

1. ...

## 可压缩成短推的版本（可选）

...
```

## When Editing an Existing Article

When the user gives an existing Markdown file:

1. Read the whole file first.
2. Identify whether the current draft is:
   - notes
   - outline
   - thread-like draft
   - article draft
   - publish-ready article
3. If it is thread-like, convert it into article paragraphs.
4. Preserve strong original lines.
5. Move meta notes to appendices.
6. Keep reader-facing正文 clean and complete.
7. Write the final Markdown back to the file.
8. Run lints or basic Markdown sanity checks when available.

## When Creating a New Article

When the user provides only a topic or rough notes:

1. Draft a working title.
2. Build an outline.
3. Research missing facts.
4. Write the article body.
5. Apply the anti-AI-writing pass.
6. Produce final Markdown.

## Failure Modes & Fallbacks

Encode failures explicitly. Do not silently skip a failed stage.

| Trigger | First response | Final fallback |
|---|---|---|
| Target Markdown file does not exist | Search nearby paths by filename | Ask the user for the correct path; do not create a replacement unless asked |
| User provides only rough notes and no title | Draft a working title from the thesis | Use `未命名_X长文.md` only if no usable title can be inferred |
| Web research returns weak or conflicting sources | Mark the claim as unverified and avoid strong wording | Move the claim to author notes or remove it from正文 |
| A local/private source informed the draft | Use it for context only | Do not expose local file names or private source names in reader-facing正文 unless requested |
| Outline is too broad | Split into 2-4 possible article angles | Trigger Checkpoint 1 and ask which angle to use |
| Article reads like a thread | Merge sentence fragments into natural paragraphs | Re-run readability review before final write |
| Anti-AI-writing score is <40/50 | Rewrite once using Stage 2 checks | Mark `needs human review` in completion note if still <40 |
| Polishing removes the user's voice | Restore first-person details and concrete phrasing | Keep authentic roughness over polished corporate prose |
| Final Markdown exceeds X long-form comfort length | Tighten examples and move references to the end | Keep the core thesis; do not split into thread unless user asks |
| Linter reports errors after editing | Fix clear Markdown/path errors | Report unresolved issues without pretending success |

## Anti-Patterns to Avoid

- Turning every sentence into its own paragraph.
- Mixing research notes with reader-facing正文.
- Adding off-topic publishing materials that the user did not request.
- Using generic AI phrases like “本文将深入探讨”.
- Over-polishing the user’s voice into corporate prose.
- Exposing local/private source names when the article should cite public sources only.
- Treating X long-form as a tweet thread.

## Completion Report

After finishing, report briefly:

```text
已完成：{file_path}
- 文章排版：自然段 / X 长文
- 去 AI 味：{score}/50
- 检查：{lints / keyword scan / references}
```

Keep the final chat response concise. The main deliverable is the Markdown file.
