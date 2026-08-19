# Snow Bilibili Summary - B站视频内容总结助手

> 输入一个 B站视频链接，自动提取字幕、评论和基本信息，快速生成结构化内容总结。

## 功能特性

| 功能 | B站 |
|------|:---:|
| 视频基本信息（标题、作者、播放量等） | ✅ |
| AI 字幕 / 字幕提取 | ✅ |
| 热门评论（按热度排序） | ✅ 50条 |
| 结构化内容总结 | ✅ |

**核心场景**：快速掌握 B站 UP 主的视频内容，无需看完整个视频。

## 快速开始

### 1. 安装 Skill

将 `snow-bilibili-summary` 文件夹放到你的 skills 目录：

```bash
# WorkBuddy 用户
cp -r snow-bilibili-summary ~/.workbuddy/skills/

# OpenClaw 用户
cp -r snow-bilibili-summary ~/.agents/skills/
```

### 2. 开始使用（开箱即用）

直接在对话中发送 B站链接即可：

```
请总结这个视频：https://www.bilibili.com/video/BVxxxxxx/
```

AI 助手会自动完成环境初始化（首次使用时创建 Python venv、安装依赖），然后提取视频内容并生成总结。**无需手动运行任何安装命令**。

### 3. 配置 B站 Cookie（可选但推荐）

B站 AI 字幕需要登录状态才能获取。不配置 Cookie 也能用，但字幕可能为空。

**自动导出（推荐）**：确保已在 Chrome 中登录 bilibili.com，运行：

```bash
~/.workbuddy/skills/snow-bilibili-summary/venv/bin/yt-dlp \
  --cookies-from-browser chrome \
  --cookies ~/.workbuddy/skills/snow-bilibili-summary/cookies.txt \
  --skip-download "https://www.bilibili.com"
```

macOS 会弹出 Keychain 授权窗口，点击"允许"即可。

**手动导出**：
1. Chrome 安装 [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 扩展
2. 打开 bilibili.com 并登录
3. 导出 cookies.txt 保存到 `~/.workbuddy/skills/snow-bilibili-summary/cookies.txt`

### 4. 开始使用

在对话中直接发送 B站链接：

```
请总结这个视频：https://www.bilibili.com/video/BVxxxxxx/
```

搜索 B站某个主题的热门视频并批量分析：

```
搜索 B站上关于"seedance 角色卡"的热门视频，提取 TOP10 并生成学习笔记
```

或者指定操作：

```
提取这个视频的字幕：https://www.bilibili.com/video/BVxxxxxx/
提取这个视频的热门评论：https://www.bilibili.com/video/BVxxxxxx/
```

## 输出示例

```markdown
# 📺 视频总结：Seedance2.0 九宫格连续漫剧教程

## 基本信息
- **作者**: 阿P手把手教会你AI
- **平台**: B站
- **播放量**: 97,991 | **点赞**: 4,647 | **收藏**: 9,030
- **时长**: 16:54

## 内容概要
本期视频是关于 Seedance 2.0 AI 视频生成工具的进阶教程...

## 核心要点
1. 九宫格分镜图 + 角色卡 + 尾帧衔接的连续创作方法
2. 三大避坑经验：不输时间线、台词固定角色、比例一致
3. 通过 Coze API 调用成本降至 1/3
...

## 精选评论
> 真大佬是承认问题，并指出问题...

## 一句话总结
一篇实操性极强的 Seedance 2.0 进阶教程...
```

## 工作原理

### 场景 A: 搜索 + 批量分析

```
用户提出主题研究需求
       ↓
  Step A1: 用 B站搜索 API 搜索关键词（支持多组关键词）
       ├── 排序方式: 综合/播放量/最新/弹幕/收藏
       ├── 时长筛选: 全部/<10分钟/10-30分钟/30-60分钟/>60分钟
       └── 返回: 标题/作者/播放量/弹幕/收藏/时长/发布日期/链接
       ↓
  Step A2: 对 TOP N 视频逐个提取数据（间隔 2 秒以上）
       ↓
  Step A3: AI 综合分析所有视频，生成主题学习笔记
```

### 场景 B: 单视频总结

```
用户发送 B站视频链接
       ↓
  Step B1: 识别 B站链接
       ↓
  Step B2: 运行 video_extractor.py 提取数据
       ├── B站 API 获取视频信息
       ├── B站 API + Cookie 获取 AI 字幕
       ├── 回退: yt-dlp + Cookie 下载字幕
       └── B站 API 获取热门评论
       ↓
  Step B3: AI 基于提取数据生成结构化总结
       ↓
  Step B4: 保存为智能命名的 .md 文件
```

## 技术细节

### B站 API 接口

| 接口 | 用途 | 是否需要 Cookie |
|------|------|:---:|
| `/x/web-interface/search/type` | 视频搜索 | 否 |
| `/x/web-interface/view` | 视频基本信息 | 否 |
| `/x/player/wbi/v2` | 字幕列表 | 是 |
| `/x/v2/reply/main` | 热门评论 | 否 |
| `/x/web-interface/nav` | WBI 签名密钥 | 否 |

### WBI 签名

B站 Web API 从 2023 年 3 月起需要 WBI 签名鉴权（`w_rid` + `wts` 参数）。本工具已内置完整的签名实现，无需额外配置。

### 字幕获取优先级

1. B站 API 直接获取 AI 字幕 JSON（需要 Cookie）
2. yt-dlp + Cookie 下载 SRT 字幕（回退方案）
3. 无字幕时，基于视频描述和评论生成总结

## 系统要求

| 依赖 | 必需 | 安装方式 |
|------|:---:|---------|
| Python 3.8+ | ✅ | `brew install python3` |
| requests | ✅ | setup.sh 自动安装 |
| yt-dlp | ✅ | setup.sh 自动安装 |
| ffmpeg | 可选 | `brew install ffmpeg` |
| whisper | 可选 | `brew install whisper-cpp` |

- **操作系统**：macOS / Linux（Windows 未测试）
- **网络**：需要访问 bilibili.com

## 文件结构

```
snow-bilibili-summary/
├── SKILL.md                  # Skill 配置文件（AI 助手读取）
├── README.md                 # 使用说明文档（人类阅读）
├── scripts/
│   ├── setup.sh              # 一键部署脚本
│   └── video_extractor.py    # 核心数据提取脚本
├── venv/                     # Python 虚拟环境（setup.sh 自动创建）
└── cookies.txt               # B站 Cookie 文件（用户自行配置）
```

## 常见问题

### Q: 字幕提取为空？

可能原因：
1. **未配置 Cookie**：B站 AI 字幕需要登录状态，请按上方说明配置
2. **Cookie 已过期**：重新运行导出命令刷新 Cookie
3. **视频没有字幕**：该 UP 主未开启 AI 字幕功能，此时会基于视频描述和评论生成总结

### Q: Cookie 过期了怎么办？

重新运行导出命令即可：
```bash
~/.workbuddy/skills/snow-bilibili-summary/venv/bin/yt-dlp \
  --cookies-from-browser chrome \
  --cookies ~/.workbuddy/skills/snow-bilibili-summary/cookies.txt \
  --skip-download "https://www.bilibili.com"
```

### Q: 支持哪些链接格式？

- `https://www.bilibili.com/video/BVxxxxxx/`
- `https://www.bilibili.com/video/BVxxxxxx/?spm_id_from=...`（带追踪参数也可以）
- `https://b23.tv/xxxxxx`（B站短链接）

### Q: 搜索功能怎么用？

直接在对话中说"搜索 B站上关于 XX 的视频"即可。搜索支持：
- **5 种排序方式**：综合、播放量、最新发布、弹幕数、收藏数
- **时长筛选**：全部、<10分钟、10-30分钟、30-60分钟、>60分钟
- **批量分析**：搜索结果可直接进入批量提取和综合分析流程

也可以手动调用脚本：
```bash
# 按播放量搜索 TOP 10
python3 scripts/video_extractor.py search "关键词" --order click --max-results 10
```

## 许可说明

- 本工具仅供个人学习和研究使用
- 请尊重内容创作者的版权
- 不要高频调用以避免触发平台反爬机制
