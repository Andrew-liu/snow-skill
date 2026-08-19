---
name: snow-bilibili-summary
description: B站视频搜索与内容总结助手。支持按关键词搜索B站视频（按播放量/最新/弹幕/收藏排序），提取视频字幕、评论区内容和基本信息，快速生成结构化总结。字幕提取采用 4 路径 fallback 策略（B站三种 API 接口 + Faster Whisper 本地 ASR 兜底），保证字幕成功率最大化，能处理 UP 主未开 AI 字幕的视频。帮助用户高效学习 UP 主的视频内容。
read_when:
  - 用户提供了 B站 (bilibili) 视频链接
  - 用户想要总结视频内容
  - 用户想要提取视频字幕或评论
  - 用户提到视频摘要、视频总结、视频笔记
  - 用户提到 BV 号或视频分析
  - 用户想要搜索 B站视频
  - 用户想要查找 B站上某个主题的热门视频
  - 用户提到搜索B站、B站搜索、bilibili搜索
  - 用户要求批量分析某个主题的B站视频
  - 用户提到视频语音转文字、ASR、Whisper、视频转录
  - 用户提到"视频没字幕怎么办"、"提取视频音频文字"
---

# Snow Bilibili Summary - B站视频内容总结助手

一键提取 B站视频的字幕、评论和基本信息，并生成结构化内容总结。

## 支持平台

- **B站 (Bilibili)**: 完整支持字幕提取、评论抓取、视频信息获取

## 前置依赖

运行以下命令检查/安装依赖：
```bash
bash {{BASE_DIR}}/scripts/setup.sh
```

依赖清单：
- **Python 3.8+**: 核心运行环境
- **ffmpeg**: 音视频处理（`brew install ffmpeg`）
- **yt-dlp**: 视频下载工具（skill venv 已内置）
- **httpx**（可选）: B 站 API 异步抓取
- **faster-whisper**（可选，仅启用 ASR 时需要）: 本地语音识别
- **NVIDIA GPU + CUDA**（可选）: 大幅加速 ASR

## 字幕提取策略（4 路径 fallback）

```
路径 1: /x/player/wbi/v2  (带 wbi 签名标准接口) →
路径 2: /x/player/v2      (无签名，部分视频独占) →
路径 3: /x/v2/dm/view     (弹幕接口附带字幕，B 站隐藏入口) →
路径 4: yt-dlp 字幕下载   (B 站 cookie 鉴权字幕) →
路径 5: Faster Whisper ASR (本地音频转文字，需 --enable-asr)
```

历史教训：单一 API 路径会误判"视频无字幕"。实测某些视频在 wbi/v2 + player/v2 都返回空，但 dm/view 有完整字幕。

### ASR 使用方式

```bash
# 默认不启用 ASR（避免误下载大文件）
python scripts/video_extractor.py extract <url> --no-comments

# 启用 ASR 兜底（前 4 路全失败时下载音频转写）
python scripts/video_extractor.py extract <url> --enable-asr

# 无 GPU / 无显卡时使用 CPU + int8（速度 ~0.3x 实时）
python scripts/video_extractor.py extract <url> --enable-asr \
    --asr-model medium --asr-device cpu --asr-compute-type int8

# 模型推荐：
# - GPU (RTX 2060+/8GB): large-v3 + cuda + float16  (5x 实时)
# - GPU (GTX 1060/6GB):  medium   + cuda + int8     (3x 实时)
# - CPU only:            medium   + cpu  + int8     (0.3x 实时)
```

### ASR 独立使用（已下载音频）

如果已用 yt-dlp 自行下载音频，可直接调用 ASR 脚本：

```bash
python scripts/asr_bilibili.py --audio /path/to/BV1xx.m4a \
    --title "视频标题" --output ./subtitles
```

## Cookie 配置（重要）

B站字幕接口**要求登录状态**才能返回 AI 字幕数据。有两种方式配置 Cookie：

### 方式一：从 Chrome 浏览器自动导出（推荐）

确保已在 Chrome 中登录 bilibili.com，然后运行：
```bash
{{BASE_DIR}}/venv/bin/yt-dlp --cookies-from-browser chrome --cookies {{BASE_DIR}}/cookies.txt --skip-download "https://www.bilibili.com"
```
系统会弹出 Keychain 授权窗口，点击"允许"即可。Cookie 文件会自动保存。

### 方式二：手动导出

1. 在 Chrome 安装 "Get cookies.txt LOCALLY" 扩展
2. 打开 bilibili.com，导出 cookies.txt
3. 保存到 `{{BASE_DIR}}/cookies.txt`

## 使用方式

### 1. 自动模式（推荐）

当用户提供视频链接时，自动识别平台并执行提取和总结：

```
请总结这个视频：https://www.bilibili.com/video/BV18QcEzWEoM/
```

### 2. B站搜索 + 批量分析

搜索 B站视频并批量提取分析：

```
搜索 B站上关于"seedance 角色卡"的热门视频，提取 TOP10 并分析
```

### 3. 仅提取字幕

```
请提取这个视频的字幕：https://www.bilibili.com/video/BVxxxxxx/
```

### 4. 仅提取评论

```
请提取这个视频的热门评论：https://www.bilibili.com/video/BVxxxxxx/
```

## 工作流程

### 场景 A: 搜索 B站视频

当用户要求搜索某个主题的 B站视频时：

#### Step A1: 执行搜索

```bash
{{BASE_DIR}}/venv/bin/python3 {{BASE_DIR}}/scripts/video_extractor.py search "<关键词>" --order <排序> --max-results <数量>
```

**参数说明**：
- `keyword`: 搜索关键词（必填）
- `--order`: 排序方式
  - `totalrank`: 综合排序（默认，推荐用于发现优质内容）
  - `click`: 按播放量排序（推荐用于找热门视频）
  - `pubdate`: 按最新发布（推荐用于跟踪最新内容）
  - `dm`: 按弹幕数量（推荐用于找互动活跃视频）
  - `stow`: 按收藏数量（推荐用于找实用教程）
- `--max-results`: 最大结果数（默认20，最大可设100）
- `--duration`: 时长筛选 0(全部) 1(<10分钟) 2(10-30分钟) 3(30-60分钟) 4(>60分钟)

**搜索策略建议**：
- 用**多组关键词**搜索同一主题以提高覆盖率，例如搜索"角色参考图"时，同时搜索"角色卡"、"角色设定"、"人物一致性"
- 对结果按播放量去重排序，选出 TOP N

脚本输出 JSON 格式，包含每个视频的 bvid、标题、作者、播放量、弹幕数、收藏数、时长、发布日期、链接等。

#### Step A2: 批量提取（控制频率）

对筛选出的视频列表，逐个执行提取（**每个视频之间间隔 2 秒以上**以避免触发限流）：

```bash
{{BASE_DIR}}/venv/bin/python3 {{BASE_DIR}}/scripts/video_extractor.py extract "<视频URL>"
```

**重要**：批量提取时必须控制频率，建议每次提取间隔 2-3 秒。

#### Step A3: 综合分析并生成报告

将所有视频的字幕、评论等信息综合分析，生成主题学习笔记。

### 场景 B: 单视频总结

### Step B1: 平台识别与链接解析

根据 URL 自动识别 B站链接：
- `bilibili.com/video/BV*` → B站
- `b23.tv/*` → B站短链接

### Step B2: 执行数据提取脚本

运行核心提取脚本（使用 skill 自带的 venv）：

```bash
{{BASE_DIR}}/venv/bin/python3 {{BASE_DIR}}/scripts/video_extractor.py "<视频URL>" --output-dir "/tmp/video_summary"
```

脚本会输出 JSON 格式数据到 stdout，包含：
- `platform`: 平台标识 (bilibili)
- `video_info`: 视频基本信息（标题、作者、播放量、点赞等）
- `subtitles`: 字幕文本（完整文本 + 带时间戳的分段）
- `comments`: 热门评论列表（最多50条）
- `error`: 错误信息（如有）

### Step B3: 生成结构化总结

基于提取的数据，生成以下格式的 Markdown 总结：

```markdown
# 📺 视频总结：{视频标题}

## 基本信息
- **作者**: {UP主/作者名}
- **平台**: B站
- **播放量**: {播放量} | **点赞**: {点赞数} | **评论**: {评论数}
- **发布时间**: {发布时间}
- **视频链接**: {原始链接}

## 内容概要
{基于字幕文本生成的 200-400 字概要，提炼核心观点}

## 核心要点
1. {要点1}
2. {要点2}
3. {要点3}
...

## 详细内容
{基于字幕的详细内容整理，按逻辑章节组织}

## 精选评论
{挑选有价值的热门评论，展示观众视角}

## 一句话总结
{一句话概括视频核心价值}
```

### Step B4: 保存报告

将生成的总结保存为 Markdown 文件到当前工作目录。

**文件命名规则**（按优先级）：
1. 基于内容生成一个简短的中文标题（10-20字，概括视频核心主题），例如：`Seedance2.0九宫格连续漫剧教程.md`
2. 如果无法智能提炼，使用视频原标题的精简版（去掉感叹号、特殊符号，截取关键词）
3. 标题中不要包含 BV 号、视频 ID 等不可读的编码

**命名示例**：
- ✅ `Seedance2.0九宫格连续漫剧教程.md`
- ✅ `360度全景图解决AI视频场景一致性.md`
- ❌ `BV18QcEzWEoM_视频总结.md`
- ❌ `独家！我居然用seedance2.0测出了长篇幅漫剧的焚决.md`（太长）

## 技术说明

### B站数据提取
- 使用 B站公开 API 提取视频信息、AI 字幕和评论
- 字幕优先级：AI 生成中文字幕 > 手动上传中文字幕 > 其他语言字幕
- 如无 API 字幕可用，回退到 yt-dlp 下载音频 + whisper 转录
- 评论通过 `/x/v2/reply/main` 接口获取，按热度排序

### 错误处理
- 链接无效：提示用户检查链接格式
- 字幕不可用：提示用户视频可能没有字幕，建议使用 whisper 转录
- 网络错误：自动重试，最多 3 次
- API 限流：提示用户稍后再试

## 注意事项

- 本工具仅供个人学习和研究使用
- 请尊重内容创作者的版权
- 不要高频调用以避免触发平台反爬机制
- B站部分接口可能需要 Cookie 才能获取完整数据
