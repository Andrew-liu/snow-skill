---
name: snow-ip
description: This skill should be used when creating a reusable personal IP character from a user's photo, revising and confirming the character, managing local character packages, and generating consistent 16:9 article illustrations with that confirmed character. It supports character sheets, clean character references, article illustration planning, Markdown insertion on request, and local asset management.
---

# Snow IP

Create reusable personal IP characters and use confirmed characters to generate consistent article illustrations.

Use this as a continuous workflow:

1. Create a character from a user-provided person photo.
2. Stop for explicit user confirmation.
3. Save the confirmed character as local reusable IP.
4. Use the confirmed character to generate article illustrations.

Do not split this into separate skills. Do not generate article illustrations before the character is confirmed.

## Every Run

1. Read `references/character-package.md` first to determine the runtime root, character state, and current character.
2. Route the user request to the right stage.
3. Read only the reference files needed for the active stage.
4. When the user asks for “我的个人 IP” or needs the bundled reference character, read `references/my-ip-character-spec.md` as the textual identity reference. This repository intentionally does not include original/generated character images.


## First-Use Guide

When the user only invokes this skill, provides no photo or article, and no confirmed character exists in the runtime root, send this brief guide and do not call image generation tools:

```text
欢迎使用 Snow IP。

请上传一张清晰的人物照片，并告诉我角色名称或昵称。

接下来我会：
1. 生成主角色和正面、左侧、背面、右侧设定图；
2. 生成干净人物参考图；
3. 请你确认或提出修改；
4. 确认后，用这个角色为文章自动配图。
```

If a confirmed current character already exists, do not ask for a new photo. Briefly state the active character name and ask for an article, idea, link, or file.

## Stage Routing

- User only invokes the skill, provides no photo/article, and no confirmed character exists: enter First-Use Guide.
- User uploads a person photo and asks to create an IP: enter Create Character.
- Current character is `draft` and user requests appearance changes: enter Revise Character.
- User explicitly says “确认”, “就用这个”, “定稿”, or equivalent: enter Confirm Character.
- User provides article, idea, link, or file and a confirmed character exists: enter Article Illustration.
- User asks to list, import, switch, or inspect characters: enter Character Management.
- User provides both photo and article but no confirmed character exists: create the character first and stop at confirmation; do not generate article illustrations yet.
- User asks for article illustrations without a confirmed character: ask the user to upload a photo and create a character first.

## Create Character

Read:

- `references/ip-builder.md`
- `references/character-package.md`
- `references/tool-workflow.md`

Procedure:

1. Use the uploaded real-person photo as the only identity source. If the user does not provide a character name, ask only for the name or nickname.
2. Extract observable visual traits: face shape, facial proportions, hairstyle, hairline, skin tone, age impression, body silhouette, fixed clothing, shoes, accessories, and overall vibe.
3. Call the image generation tool to create a vertical character sheet: one main full-body character plus front, left-side, back, and right-side views.
4. Generate a clean single-person full-body reference image with transparent or pure white background. Do not copy the sheet title, borders, multi-view layout, labels, or base.
5. Write `character-spec.md` with only observable and reusable fixed visual traits. Do not infer sensitive attributes or private identity.
6. Register the three outputs as a `draft` character package. Prefer `scripts/character_registry.py register`; if the script is unavailable, manually create the same structure described in `references/character-package.md`.
7. Show the character sheet and clean reference, report the character package path, and ask only whether the user wants to confirm or revise.

Draft characters must not be activated. Do not skip confirmation even if the user provides an article at the same time.

## Revise Character

1. Read the current draft character sheet, clean reference, and character spec.
2. Convert the user's requested change into one explicit visual modification. Keep all unmentioned identity traits unchanged.
3. Pass the edit target, original photo if still accessible, and current clean reference into the image editing workflow.
4. Fix only one major issue per revision.
5. Re-check consistency between main view and four-view sheet.
6. Save as a new version, register again as `draft`, and wait for confirmation.

## Confirm Character

1. Execute only after explicit user confirmation.
2. Check that character sheet, clean reference, and character spec all exist.
3. Run:

```bash
python3 scripts/character_registry.py confirm --root <runtime-root> --slug <character-slug>
```

4. Mark the character as `confirmed` and update `current-character.json`.
5. Tell the user the character is ready for article illustrations.

## Article Illustration

Read:

- `references/article-workflow.md`
- `references/illustration-style.md`
- `references/tool-workflow.md`
- the current character package's `character-spec.md`

Procedure:

1. Use `scripts/character_registry.py resolve` to resolve the requested character or current character. Use only `confirmed` characters.
2. Read the full article or full input. Do not infer the full article from title or snippet only.
3. Decide image count by information density, unless the user specifies a count.
4. Choose a different cognitive anchor for each image.
5. For each image, choose either `流程拆解` or `核心动作`.
6. Use the current character's clean reference as the default identity reference. Add character sheet only when side/back/multi-angle verification is needed.
7. Call image generation separately for every cognitive anchor. Inspect and save each image. Do not use one collage as a substitute for multiple images.
8. Report each image's purpose, actual absolute path, and suggested insertion position. Do not modify the source article by default.

## Character Management

- List characters: `python3 scripts/character_registry.py list --root <runtime-root>`.
- Switch character: `python3 scripts/character_registry.py activate --root <runtime-root> --slug <character-slug>`.
- Inspect current character: `python3 scripts/character_registry.py resolve --root <runtime-root>`.
- Do not activate `draft` characters.
- Keep historical images for same-name revisions; the manifest points to the latest version.

## Image Tool Requirements

- Use the host's built-in image generation tool or an equivalent image generation/editing interface.
- For new images, pass the clean identity reference. For edits, pass both the edit target and identity reference.
- During character creation, use the photo only for identity reference. Do not copy the original background, other people, text, watermark, or unrelated objects.
- Article illustrations must not copy the character sheet's background, title, border, direction labels, or multi-view layout.
- If the tool cannot save to the target directory, keep the actual returned path and report it honestly.
- If the host has no image generation capability, output executable prompts, reference paths, and a save plan; clearly state that images were not generated.

## Privacy and Boundaries

- Do not copy the original person photo into the character package by default.
- Keep character packages and article illustrations in the user's local runtime root.
- Do not infer name, occupation, ethnicity, health, political orientation, religion, sexual orientation, or other sensitive attributes from a photo.
- Do not overwrite existing character assets or illustrations; use `-v2`, `-v3`, and so on.
- Only write image links into the original article when the user explicitly asks.
