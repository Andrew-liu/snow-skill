<div align="center">

# Snow Skill

> 个人常用 Agent Skill 集合：内容提取、长文写作与轻量工作流封装。

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Snow-blueviolet?style=flat-square)](#当前-skills)

[当前 Skills](#当前-skills) · [安装方式](#安装方式) · [使用示例](#使用示例)

</div>

---

## 这个仓库是什么

`snow-skill` 用来存放可复用的个人 Agent Skills。每个 Skill 都是一个独立目录，包含 `SKILL.md` 和必要的脚本、参考资料或说明文件。

设计原则：

- **可复制**：每个 Skill 可以单独复制到本地 Skill 目录使用。
- **可审计**：脚本、依赖和触发场景尽量写清楚。
- **少依赖**：能自包含就自包含，避免安装后还要额外找其他 Skill。

## 当前 Skills

| Skill | 用途 | 依赖特点 |
|---|---|---|
| [`snow-bilibili-summary`](snow-bilibili-summary/) | B站视频搜索、字幕提取、评论抓取和结构化总结 | 自带脚本；需要 Python 运行环境 |
| [`snow-x-article`](snow-x-article/) | X/Twitter 长文写作、改写、去 AI 味和 Markdown 输出 | 自包含版本；已去掉外部 Skill 依赖和配图流程 |

## 安装方式

在支持 Skills CLI 的 ChatGPT / Codex 环境中，用 `npx` 安装需要的 Skill：

```bash
npx skills add Andrew-liu/snow-skill -s snow-bilibili-summary -g
npx skills add Andrew-liu/snow-skill -s snow-x-article -g
```

这个仓库包含多个 Skill，使用 `-s` 指定要安装的 Skill 名称；只需要其中一个时，运行对应那一行即可。


## 使用示例

### B站视频总结

```text
请总结这个视频：https://www.bilibili.com/video/BVxxxxxx/
```

```text
搜索 B站上关于“AI Agent 面试”的热门视频，提取 TOP10 并生成学习笔记
```

### X 长文写作

```text
@command://snow-x-article 根据这些笔记写一篇 X 长文，主题是 Code Agent 为什么需要 RAG。
```

```text
@command://snow-x-article 重写这篇文章，保留我的语气，去掉 AI 味 @/path/to/article.md
```





## License

[MIT](LICENSE)