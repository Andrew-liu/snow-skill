#!/bin/bash
# ============================================================
# Snow Bilibili Summary - 一键部署脚本
# 自动检测环境、创建虚拟环境、安装依赖、引导配置 Cookie
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${SKILL_DIR}/venv"
COOKIE_FILE="${SKILL_DIR}/cookies.txt"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   Snow Bilibili Summary - 一键部署         ║${NC}"
echo -e "${BOLD}║   B站视频内容提取与总结工具                ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""

ALL_OK=true
NEED_VENV=false

# ============================================================
# Step 1: 检查 Python
# ============================================================
echo -e "${BLUE}[1/4] 检查系统依赖${NC}"
echo ""

echo -n "  Python3 ........... "
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1)
    echo -e "${GREEN}✓ ${PY_VER}${NC}"
else
    echo -e "${RED}✗ 未安装${NC}"
    echo "  → 请先安装 Python 3.8+: brew install python3"
    ALL_OK=false
fi

echo -n "  ffmpeg ............. "
if command -v ffmpeg &>/dev/null; then
    echo -e "${GREEN}✓ 已安装${NC}"
else
    echo -e "${YELLOW}⚠ 未安装（可选，ASR 音频处理需要）${NC}"
    echo "  → 安装: brew install ffmpeg"
fi

echo -n "  whisper ............ "
if command -v whisper &>/dev/null || command -v whisper-cpp &>/dev/null; then
    echo -e "${GREEN}✓ 已安装${NC}"
else
    echo -e "${YELLOW}⚠ 未安装（可选，ASR 语音转录需要）${NC}"
    echo "  → 安装: brew install whisper-cpp"
fi

echo ""

if [ "$ALL_OK" = false ]; then
    echo -e "${RED}核心依赖缺失，请先安装后重新运行。${NC}"
    exit 1
fi

# ============================================================
# Step 2: 创建虚拟环境并安装依赖
# ============================================================
echo -e "${BLUE}[2/4] 配置 Python 虚拟环境${NC}"
echo ""

if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python3" ]; then
    echo -e "  虚拟环境 .......... ${GREEN}✓ 已存在${NC}"

    # 检查依赖
    NEED_INSTALL=false
    if ! "$VENV_DIR/bin/python3" -c "import requests" 2>/dev/null; then
        NEED_INSTALL=true
    fi
    if ! [ -f "$VENV_DIR/bin/yt-dlp" ]; then
        NEED_INSTALL=true
    fi

    if [ "$NEED_INSTALL" = true ]; then
        echo "  正在安装缺失的依赖..."
        "$VENV_DIR/bin/pip" install -q requests yt-dlp 2>/dev/null
        echo -e "  依赖安装 .......... ${GREEN}✓ 完成${NC}"
    else
        echo -e "  依赖检查 .......... ${GREEN}✓ requests + yt-dlp 已就绪${NC}"
    fi
else
    echo "  正在创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
    echo "  正在安装依赖 (requests, yt-dlp)..."
    "$VENV_DIR/bin/pip" install -q --upgrade pip 2>/dev/null
    "$VENV_DIR/bin/pip" install -q requests yt-dlp 2>/dev/null
    echo -e "  虚拟环境 .......... ${GREEN}✓ 创建完成${NC}"
    echo -e "  依赖安装 .......... ${GREEN}✓ requests + yt-dlp 已安装${NC}"
fi

echo ""

# ============================================================
# Step 3: Cookie 配置
# ============================================================
echo -e "${BLUE}[3/4] Cookie 配置（B站字幕提取需要）${NC}"
echo ""

if [ -f "$COOKIE_FILE" ]; then
    # 检查 cookie 文件是否包含 bilibili 相关内容
    if grep -q "bilibili" "$COOKIE_FILE" 2>/dev/null; then
        echo -e "  Cookie 文件 ....... ${GREEN}✓ 已配置 (${COOKIE_FILE})${NC}"
    else
        echo -e "  Cookie 文件 ....... ${YELLOW}⚠ 文件存在但可能不包含 B站 Cookie${NC}"
    fi
else
    echo -e "  Cookie 文件 ....... ${YELLOW}⚠ 未配置${NC}"
    echo ""
    echo "  B站 AI 字幕需要登录 Cookie 才能获取。"
    echo "  没有 Cookie 仍可获取视频信息和评论，但字幕可能为空。"
    echo ""
    echo "  配置方式（二选一）："
    echo ""
    echo "  ${BOLD}方式一：自动从 Chrome 导出（推荐）${NC}"
    echo "  确保已在 Chrome 中登录 bilibili.com，然后运行："
    echo "  ${VENV_DIR}/bin/yt-dlp --cookies-from-browser chrome \\"
    echo "    --cookies ${COOKIE_FILE} --skip-download \"https://www.bilibili.com\""
    echo ""
    echo "  ${BOLD}方式二：手动导出${NC}"
    echo "  1. Chrome 安装 'Get cookies.txt LOCALLY' 扩展"
    echo "  2. 打开 bilibili.com → 导出 cookies.txt"
    echo "  3. 保存到: ${COOKIE_FILE}"
fi

echo ""

# ============================================================
# Step 4: 验证
# ============================================================
echo -e "${BLUE}[4/4] 部署验证${NC}"
echo ""

# 测试脚本是否可运行
EXTRACTOR="${SKILL_DIR}/scripts/video_extractor.py"
if [ -f "$EXTRACTOR" ]; then
    TEST_OUTPUT=$("$VENV_DIR/bin/python3" "$EXTRACTOR" --help 2>&1 | head -1)
    if echo "$TEST_OUTPUT" | grep -q "usage\|视频"; then
        echo -e "  提取脚本 .......... ${GREEN}✓ 可正常运行${NC}"
    else
        echo -e "  提取脚本 .......... ${YELLOW}⚠ 运行异常，请检查 Python 环境${NC}"
    fi
else
    echo -e "  提取脚本 .......... ${RED}✗ 文件不存在${NC}"
fi

echo ""
echo -e "${BOLD}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo ""
echo "使用方式：在对话中直接发送 B站视频链接即可自动触发。"
echo ""
echo "示例："
echo "  请总结这个视频：https://www.bilibili.com/video/BVxxxxxx/"
echo ""
echo -e "${BOLD}══════════════════════════════════════════════${NC}"
