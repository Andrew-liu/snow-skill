---
name: snow-x-article
description: This skill should be used when writing, rewriting, researching, polishing, or packaging long-form X/Twitter articles in Markdown. It preserves the user's voice, supports research and citation management, applies a self-contained anti-AI-writing editorial pass, and produces a final Hexo-compatible long-form Markdown article. Trigger on "X长文", "推特长文", "写长文", "改长文", "重写文章", "生成X长文", or @command://snow-x-article.
---

# Snow X Article

Create publication-ready **long-form articles** in a single canonical format: Hexo-compatible Markdown that doubles as an X long-form source. Treat this as an editorial workflow, not a tweet/thread generator.

Core promise:

1. Preserve the user's voice and strongest original lines.
2. Research missing facts when needed and keep claims traceable.
3. Convert notes, outlines, or thread-like drafts into natural long-form article paragraphs.
4. Apply a self-contained anti-AI-writing pass before final delivery.
5. Produce one clean Hexo-ready Markdown file. No alternative output formats.

## Canonical File Format (mandatory, the only format)

Every article file MUST follow this exact structure:

```markdown
---
title: 文章标题（不写在正文里）
date: YYYY-MM-DD 12:00:00
tags: [标签1, 标签2, 标签3]
---

> 基于 / 实测机器 / 说明 等有读者价值的元信息（可选，逐行 blockquote）

开场简介：1-4 个自然段，直接进入主题，兼作博客首页摘要。

<!-- more -->

## 01｜第一个章节标题

正文自然段。

## 02｜第二个章节标题

正文自然段。

---

## 参考来源（可选）

1. [公开可访问的引用](https://...)
```

Format rules, all mandatory:

- **Front-matter**: `title` holds the article title. `date` is the writing day plus fixed time `12:00:00`. `tags` are 3-5 items the model derives from the topic, in `[a, b, c]` inline array form.
- **No H1 in body**. The title lives only in front-matter. Never write `# 标题` in the body.
- **No `## X 长文正文` or similar wrapper headings.**
- **Opening intro** sits between front-matter (or the optional blockquote meta lines) and `<!-- more -->`. It is reader-facing prose, not a work note.
- **`<!-- more -->` position is a hard rule**: always immediately before the first `## ` chapter heading. Never move it to tune excerpt length; fix the intro instead.
- **Chapters are H2 with zero-padded numbering**: `## 01｜标题`, `## 02｜标题`. Use `###` only for rare sub-steps inside a chapter (installation steps, sub-cases). Never use `## 第一章｜` word-style numbering.
- **References section is always named `## 参考来源`** (never 参考资料 / 参考链接), placed after a `---` divider at the end, optional.
- **Images** use relative paths under the article directory's image folder (for `Obsidian/02-X/` that is `./image/xxx.png`). If a referenced image does not exist, comment the reference out with a `<!-- TODO: 配图缺失 ... -->` note instead of leaving a broken link.

## Publicness Gate (mandatory final check)

The body and 参考来源 MUST NOT contain:

- drive-letter local paths (`D:/`, `G:/`, `C:\`, etc.)
- local-only file names that are not publicly accessible (private logs, local notes)
- private/internal source names, unless the user explicitly asks

Resolution order: map the local reference to its public equivalent (e.g. `D:/UGit/mini-agent/agent.py` → `https://github.com/Andrew-liu/mini-agent/blob/master/agent.py`); if no public equivalent exists, delete the reference. Verify this gate line-by-line before final write.

## Work Materials Go to Chat, Never to File

Do NOT write any of these into the article file:

- 标题备选 (alternative titles)
- 可压缩成短推的版本 (short-tweet version)
- 发布图片顺序 (image publishing order)
- research notes, publishing notes, self-scores

Instead, after the final file is written, output in the chat reply:

1. **标题备选**: 3-5 alternative titles for the user to pick from.
2. **可压缩成短推的版本**: a short-tweet compression of the article, ready to post.

These are ephemeral working materials. The file stays clean.

## Critical Writing Rules

- Do **not** write in thread style unless explicitly requested.
- Do **not** use one sentence per paragraph as the default.
- Use natural article paragraphs: target 2-5 sentences per paragraph.
- Keep short paragraphs only for emphasis, not as every line.
- Preserve the user's first-person voice and informal style when present.
- Avoid turning the article into a corporate report or academic paper unless explicitly requested.

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

### Checkpoint 1 — Outline Approval

Stop and ask for confirmation before drafting the full article when:

- the user asks to write a new long-form article from rough notes
- the topic is broad or research-heavy
- the article structure is unclear
- the output will be longer than 1,500 Chinese characters

Include in the outline for approval: working `title`, `date`, proposed `tags`, chapter list.

Skip this checkpoint only when the user explicitly asks to directly rewrite an existing file.

### Checkpoint 2 — Destructive Edit / Final Overwrite

Before overwriting an existing Markdown file:

1. Read the whole file.
2. Confirm the output path.
3. If the rewrite changes more than formatting, state that the file will be overwritten.
4. Keep a concise completion note after writing.

If the user already gave a direct command like "覆盖 / 落地到这个文件 / 重写这个文件", treat that as approval after reading the file.

## Three-Stage Workflow

### Stage 1 — Research, Outline, Voice, Citations

1. Understand the writing project: topic, main argument, audience, goal, sources to use or avoid, writing voice.
2. Build or refine an outline before writing: hook, context, main sections, examples, conclusion, citation needs.
3. Conduct research when needed:
   - use web search / web fetch for current facts
   - read user-provided local files when relevant
   - distinguish verified facts from personal interpretation
   - never cite private/local sources in the reader-facing article
4. Preserve author voice:
   - keep first-person observations and lived details
   - keep rough-but-real phrasing when it improves authenticity
   - improve clarity without replacing the user's personality
5. Manage citations:
   - use light citations; add `## 参考来源` only when the article cites papers, web articles, reports, or claims needing traceability
   - every reference must pass the Publicness Gate

### Stage 2 — Anti-AI-Writing Editorial Pass

Mandatory checks before final delivery:

1. Remove AI-like filler: "值得注意的是" when unnecessary, "在当今快速变化的时代", "让我们深入探讨", generic opening politeness.
2. Break formulaic structures: forced three-part lists, repeated "不是 X，而是 Y" patterns, mechanical setup/reveal, meaningless "从 X 到 Y" framing.
3. Remove marketing / corporate tone: 赋能、至关重要、深刻变革、不断演变的格局、里程碑式; 生态/闭环/抓手 as empty jargon.
4. Avoid dash spam: avoid `——` and overused `—`; use commas, colons, periods, or paragraph breaks instead.
5. Improve paragraph rhythm: merge isolated one-liners into real paragraphs; mix short, medium, long sentences; use headings for structure, not blank-line stacks.
6. Preserve human voice: concrete details over generic summary; keep genuine uncertainty; prefer authentic roughness over polished corporate prose.
7. Score the article after revision:

| Dimension | Meaning | /10 |
|---|---|---|
| Directness | says the point without ceremonial framing | |
| Rhythm | natural paragraph and sentence variation | |
| Trust | avoids over-explaining and fake certainty | |
| Human voice | sounds like a real person, not a generated essay | |
| Concision | removes filler while keeping substance | |

Gate: ≥45/50 ready; 40-44 polish once if easy; <40 revise before finalizing.

### Stage 3 — Final Review and Hexo-Ready Markdown

1. Format compliance (all hard rules):
   - front-matter present and complete (`title` / `date ... 12:00:00` / `tags`)
   - no H1 in body, no wrapper headings
   - `<!-- more -->` immediately before the first `## ` chapter
   - chapters numbered `## 01｜` style
   - references section (if any) named `## 参考来源` after `---`
2. Publicness Gate: scan every line for local paths and private sources; map to public links or delete.
3. Structure: hook works, sections ordered logically, no work notes mixed into正文.
4. Readability: paragraphs read like an article, no walls of text, headings useful.
5. Facts: key claims sourced or framed as opinion; uncertainties marked.
6. Anti-AI-writing: re-run Stage 2 checks after the final edit.
7. Write the file, then output 标题备选 and 短推版本 in chat (never in the file).

## When Editing an Existing Article

1. Read the whole file first.
2. Identify the draft type: notes / outline / thread-like draft / article draft / publish-ready.
3. **If the file is in a legacy format** (body H1 title, `> 主题/日期/用途` blockquote meta block, `## X 长文正文` wrapper, 标题备选 / 短推 / 发布图片顺序 blocks in file, `### 01｜` chapter levels, local paths in references), **migrate it to the canonical format automatically as part of the edit** — no separate permission needed:
   - H1 → front-matter `title`; meta block dates → front-matter `date`; 主题 line → `tags`
   - keep valuable meta lines (基于/实测机器/说明/版本) as blockquote lines under front-matter
   - delete wrapper headings and work blocks (they move to chat if freshly useful, otherwise drop)
   - promote `### NN｜` chapters to `## NN｜`; convert word-style chapter numbering to `01｜` style
   - insert `<!-- more -->` before the first chapter
   - fix image paths to the article's image folder convention; run the Publicness Gate
4. If it is thread-like, convert it into article paragraphs.
5. Preserve strong original lines.
6. Write the final Markdown back to the file.
7. Run basic Markdown sanity checks when available.

## When Creating a New Article

1. Draft a working title.
2. Build an outline (Checkpoint 1 when applicable, including title/date/tags).
3. Research missing facts.
4. Write the article body in the canonical format.
5. Apply the anti-AI-writing pass.
6. Final review, write file, deliver 标题备选 + 短推版本 in chat.

## Failure Modes & Fallbacks

| Trigger | First response | Final fallback |
|---|---|---|
| Target Markdown file does not exist | Search nearby paths by filename | Ask the user for the correct path; do not create a replacement unless asked |
| User provides only rough notes and no title | Draft a working title from the thesis | Use `未命名_X长文.md` only if no usable title can be inferred |
| Web research returns weak or conflicting sources | Mark the claim as unverified and avoid strong wording | Move the claim out of正文 or remove it |
| A local/private source informed the draft | Use it for context only | Map to a public link or delete the reference; never expose local paths |
| Referenced image file does not exist | Search the image folder for a matching file | Comment the reference out with a `<!-- TODO: 配图缺失 -->` note |
| Outline is too broad | Split into 2-4 possible article angles | Trigger Checkpoint 1 and ask which angle to use |
| Article reads like a thread | Merge sentence fragments into natural paragraphs | Re-run readability review before final write |
| Anti-AI-writing score is <40/50 | Rewrite once using Stage 2 checks | Mark `needs human review` in completion note if still <40 |
| Polishing removes the user's voice | Restore first-person details and concrete phrasing | Keep authentic roughness over polished corporate prose |
| Final Markdown exceeds X long-form comfort length | Tighten examples and move references to the end | Keep the core thesis; do not split into thread unless user asks |
| Linter reports errors after editing | Fix clear Markdown/path errors | Report unresolved issues without pretending success |

## Anti-Patterns to Avoid

- Writing the title as body H1 (it belongs in front-matter only).
- Writing 标题备选 / 短推版本 / 发布图片顺序 into the article file.
- Using `## X 长文正文` or any wrapper heading.
- Moving `<!-- more -->` to tune excerpt length.
- Leaving drive-letter paths or private source names anywhere in the file.
- Turning every sentence into its own paragraph.
- Mixing research notes with reader-facing正文.
- Using generic AI phrases like "本文将深入探讨".
- Over-polishing the user's voice into corporate prose.
- Treating X long-form as a tweet thread.

## Completion Report

After finishing, report briefly:

```text
已完成：{file_path}
- 格式：Hexo front-matter / more 标记 / H2 编号章节
- 公开性门禁：{通过 / 处理了 N 处}
- 去 AI 味：{score}/50
```

Then provide in chat: 标题备选 (3-5) and 可压缩成短推的版本. Keep the final chat response concise. The main deliverable is the Markdown file.
