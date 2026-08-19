#!/usr/bin/env python3
"""
Snow Bilibili Summary - 视频内容提取工具
支持 B站 (Bilibili) 视频的字幕、评论和基本信息提取
"""

import sys
import os
import re
import json
import time
import hashlib
import argparse
import subprocess
from urllib.parse import urlencode, quote, urlparse, parse_qs

# 尝试导入 requests，如果没有则用 urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False


# ============================================================
# HTTP 请求封装
# ============================================================

DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

def http_get(url, headers=None, timeout=15):
    """统一 HTTP GET，优先用 requests，否则用 urllib"""
    hdrs = {"User-Agent": DEFAULT_UA}
    if headers:
        hdrs.update(headers)
    if HAS_REQUESTS:
        r = requests.get(url, headers=hdrs, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r.text, r.status_code
    else:
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8"), resp.status

def http_get_json(url, headers=None, timeout=15):
    """GET 并解析 JSON"""
    text, code = http_get(url, headers, timeout)
    return json.loads(text)


# ============================================================
# 平台识别
# ============================================================

def detect_platform(url):
    """识别 B站 URL。"""
    url_lower = url.lower()
    if "bilibili.com" in url_lower or "b23.tv" in url_lower:
        return "bilibili"
    return "unknown"


# ============================================================
# B站 (Bilibili) 提取器
# ============================================================

class BilibiliExtractor:
    """B站视频数据提取器"""

    # WBI 签名的混合密钥映射表
    MIXIN_KEY_ENC_TAB = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
        27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
        37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
        22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52
    ]

    def __init__(self, cookie_str=None):
        self.session_headers = {
            "User-Agent": DEFAULT_UA,
            "Referer": "https://www.bilibili.com",
            "Origin": "https://www.bilibili.com",
        }
        if cookie_str:
            self.session_headers["Cookie"] = cookie_str
        self._img_key = None
        self._sub_key = None
        self._mixin_key = None

    # ---- BV号提取 ----
    def extract_bvid(self, url):
        """从 URL 中提取 BV 号"""
        # 处理 b23.tv 短链接
        if "b23.tv" in url:
            try:
                if HAS_REQUESTS:
                    r = requests.head(url, headers=self.session_headers, allow_redirects=True, timeout=10)
                    url = r.url
                else:
                    req = urllib.request.Request(url, headers=self.session_headers, method='HEAD')
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        url = resp.url
            except Exception:
                pass

        match = re.search(r"(BV[a-zA-Z0-9]+)", url)
        if match:
            return match.group(1)
        return None

    # ---- WBI 签名 ----
    def _get_wbi_keys(self):
        """获取 WBI 签名密钥"""
        if self._img_key and self._sub_key:
            return

        try:
            data = http_get_json(
                "https://api.bilibili.com/x/web-interface/nav",
                headers=self.session_headers
            )
            wbi_img = data.get("data", {}).get("wbi_img", {})
            img_url = wbi_img.get("img_url", "")
            sub_url = wbi_img.get("sub_url", "")

            self._img_key = img_url.split("/")[-1].split(".")[0]
            self._sub_key = sub_url.split("/")[-1].split(".")[0]

            # 生成混合密钥
            raw_key = self._img_key + self._sub_key
            self._mixin_key = "".join(
                raw_key[i] for i in self.MIXIN_KEY_ENC_TAB if i < len(raw_key)
            )[:32]
        except Exception as e:
            sys.stderr.write(f"[WARN] 获取 WBI 密钥失败: {e}\n")

    def _sign_params(self, params):
        """对参数进行 WBI 签名"""
        self._get_wbi_keys()
        if not self._mixin_key:
            return params

        params["wts"] = int(time.time())
        # 过滤特殊字符
        filtered = {}
        for k, v in params.items():
            v_str = str(v)
            for ch in "!'()*":
                v_str = v_str.replace(ch, "")
            filtered[k] = v_str
        # 排序并编码
        sorted_params = sorted(filtered.items())
        query = "&".join(f"{k}={v}" for k, v in sorted_params)
        w_rid = hashlib.md5((query + self._mixin_key).encode()).hexdigest()
        params["w_rid"] = w_rid
        return params

    # ---- 视频基本信息 ----
    def get_video_info(self, bvid):
        """获取视频基本信息"""
        params = self._sign_params({"bvid": bvid})
        url = f"https://api.bilibili.com/x/web-interface/view?{urlencode(params)}"

        data = http_get_json(url, headers=self.session_headers)
        if data.get("code") != 0:
            return None

        d = data["data"]
        stat = d.get("stat", {})
        owner = d.get("owner", {})

        return {
            "aid": d.get("aid"),
            "bvid": d.get("bvid"),
            "cid": d.get("cid"),
            "title": d.get("title", ""),
            "description": d.get("desc", ""),
            "author": owner.get("name", ""),
            "author_mid": owner.get("mid"),
            "cover": d.get("pic", ""),
            "duration": d.get("duration", 0),
            "duration_text": self._format_duration(d.get("duration", 0)),
            "pub_date": time.strftime("%Y-%m-%d %H:%M", time.localtime(d.get("pubdate", 0))),
            "views": stat.get("view", 0),
            "likes": stat.get("like", 0),
            "coins": stat.get("coin", 0),
            "favorites": stat.get("favorite", 0),
            "shares": stat.get("share", 0),
            "comments": stat.get("reply", 0),
            "danmaku": stat.get("danmaku", 0),
            "pages": [
                {"cid": p.get("cid"), "part": p.get("part", ""), "duration": p.get("duration", 0)}
                for p in d.get("pages", [])
            ],
        }

    @staticmethod
    def _format_duration(seconds):
        """格式化时长"""
        if seconds <= 0:
            return "0:00"
        h, remainder = divmod(int(seconds), 3600)
        m, s = divmod(remainder, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    # ---- 字幕提取 ----
    def _parse_subtitles_from_list(self, subtitles_list):
        """从字幕列表中选最佳并下载内容（共用逻辑，给 wbi/v2 + dm/view 两条路径复用）"""
        if not subtitles_list:
            return None
        preferred = None
        for sub in subtitles_list:
            lan = sub.get("lan", "")
            if lan in ["ai-zh", "zh-CN", "zh", "zh-Hans"]:
                preferred = sub
                break
        if not preferred:
            preferred = subtitles_list[0]

        sub_url = preferred.get("subtitle_url", "")
        if not sub_url:
            return None
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url
        elif sub_url.startswith("http://"):
            sub_url = "https://" + sub_url[7:]

        sub_data = http_get_json(sub_url, headers=self.session_headers)
        body = sub_data.get("body", [])

        segments = []
        full_text_parts = []
        for item in body:
            content = item.get("content", "").strip()
            if content:
                start = item.get("from", 0)
                end = item.get("to", 0)
                segments.append({
                    "start": start,
                    "end": end,
                    "start_text": self._format_duration(start),
                    "end_text": self._format_duration(end),
                    "text": content,
                })
                full_text_parts.append(content)

        if not segments:
            return None

        return {
            "language": preferred.get("lan_doc", "中文"),
            "language_code": preferred.get("lan", "zh"),
            "full_text": "\n".join(full_text_parts),
            "segments": segments,
            "segment_count": len(segments),
        }

    def get_subtitles(self, aid, cid, bvid=None, enable_asr=False, asr_options=None):
        """获取视频字幕（4 路径 fallback）

        多 API 策略（已内化 bilibili-subtitle-extractor 全部能力）：
        1) /x/player/wbi/v2 (带 wbi 签名，标准接口)
        2) /x/player/v2     (无签名，部分视频独占)
        3) /x/v2/dm/view    (弹幕接口附带字幕，B 站某些视频字幕仅在此返回)
        4) Faster Whisper ASR 本地语音识别（终极兜底，需 enable_asr=True）

        历史教训：单一 API 路径会误判"视频无字幕"，
        实测 BV1bH7U6PE2P / BV1mFEb66EQd 等视频
        在 wbi/v2 + player/v2 都返回空，但 dm/view 有完整字幕。

        ASR 路径说明：
        - 仅在 enable_asr=True 时启用（默认关闭，避免误下载大文件）
        - 需要 yt-dlp + faster-whisper 已安装
        - asr_options = {"model": "large-v3", "device": "cuda", "compute_type": "float16", "language": "zh"}
        """
        # ---- 路径 1: wbi/v2（带签名，老版本默认接口）----
        try:
            params = self._sign_params({"aid": aid, "cid": cid})
            url = f"https://api.bilibili.com/x/player/wbi/v2?{urlencode(params)}"
            data = http_get_json(url, headers=self.session_headers)
            if data.get("code") == 0:
                subs = data.get("data", {}).get("subtitle", {}).get("subtitles", [])
                result = self._parse_subtitles_from_list(subs)
                if result:
                    return result
        except Exception as e:
            sys.stderr.write(f"[INFO] 字幕路径1(wbi/v2) 失败，继续尝试: {e}\n")

        # ---- 路径 2: player/v2（无签名，不带 wbi）----
        if bvid:
            try:
                url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
                data = http_get_json(url, headers=self.session_headers)
                if data.get("code") == 0:
                    subs = data.get("data", {}).get("subtitle", {}).get("subtitles", [])
                    result = self._parse_subtitles_from_list(subs)
                    if result:
                        return result
            except Exception as e:
                sys.stderr.write(f"[INFO] 字幕路径2(player/v2) 失败，继续尝试: {e}\n")

        # ---- 路径 3: dm/view 弹幕接口附带字幕（B 站隐藏字幕入口）----
        try:
            url = f"https://api.bilibili.com/x/v2/dm/view?type=1&oid={cid}"
            data = http_get_json(url, headers=self.session_headers)
            if data.get("code") == 0:
                subs = data.get("data", {}).get("subtitle", {}).get("subtitles", [])
                result = self._parse_subtitles_from_list(subs)
                if result:
                    return result
        except Exception as e:
            sys.stderr.write(f"[INFO] 字幕路径3(dm/view) 失败: {e}\n")

        # ---- 路径 4: Faster Whisper ASR 本地语音识别（终极兜底）----
        if enable_asr and bvid:
            asr_result = self._try_whisper_asr(bvid, asr_options or {})
            if asr_result:
                return asr_result

        if enable_asr and not bvid:
            sys.stderr.write(f"[WARN] ASR 路径需要 bvid，跳过\n")

        sys.stderr.write(f"[WARN] 所有字幕路径均失败 (aid={aid}, cid={cid}, bvid={bvid})\n")
        if not enable_asr:
            sys.stderr.write(f"[HINT] 该视频可能无官方字幕，可加 --enable-asr 启用 Whisper 语音识别（需 yt-dlp + faster-whisper）\n")
        return None

    def _try_whisper_asr(self, bvid, options):
        """终极兜底：yt-dlp 下载音频 + Faster Whisper 本地 ASR

        options 可选键:
            model:        Whisper 模型 (默认 large-v3)
            device:       cuda / cpu (默认 cuda，无 GPU 自动降级 cpu)
            compute_type: float16 / int8 / float32 (默认 float16)
            language:     识别语言 (默认 zh)
            audio_dir:    音频临时目录 (默认 系统 temp)
        """
        try:
            import tempfile
            import shutil

            sys.stderr.write(f"[INFO] 启动 ASR 兜底链路 (bvid={bvid})...\n")

            # ---- Step 1: 下载音频 ----
            try:
                import yt_dlp as _ytdlp_mod  # noqa: F401
            except ImportError:
                sys.stderr.write(f"[WARN] yt-dlp 未安装，无法下载音频。pip install yt-dlp\n")
                return None

            audio_dir = options.get("audio_dir") or tempfile.mkdtemp(prefix="vs_asr_audio_")
            os.makedirs(audio_dir, exist_ok=True)

            # Windows 便携 ffmpeg 兜底：优先使用 imageio-ffmpeg 自带二进制，避免依赖系统 PATH。
            try:
                import imageio_ffmpeg
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                ffmpeg_dir = os.path.dirname(ffmpeg_exe)
                if os.path.isdir(ffmpeg_dir):
                    standard_ffmpeg = os.path.join(ffmpeg_dir, "ffmpeg.exe")
                    if os.name == "nt" and not os.path.exists(standard_ffmpeg) and os.path.exists(ffmpeg_exe):
                        try:
                            shutil.copyfile(ffmpeg_exe, standard_ffmpeg)
                        except Exception:
                            pass
                    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
            except Exception:
                pass

            cookie_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "cookies.txt",
            )

            ytdlp_exe = self._find_ytdlp_exe()
            if not ytdlp_exe:
                sys.stderr.write(f"[WARN] 找不到 yt-dlp 可执行文件\n")
                return None

            url = f"https://www.bilibili.com/video/{bvid}"
            output_template = os.path.join(audio_dir, "%(id)s.%(ext)s")
            cmd = [
                ytdlp_exe,
                "-x", "--audio-format", "m4a",
                "-o", output_template,
                url,
            ]
            if os.path.exists(cookie_file):
                cmd.extend(["--cookies", cookie_file])

            sys.stderr.write(f"[INFO] yt-dlp 下载音频: {bvid}\n")
            try:
                subprocess.run(cmd, capture_output=True, text=True, timeout=300, encoding="utf-8")
            except subprocess.TimeoutExpired:
                sys.stderr.write(f"[WARN] yt-dlp 下载超时 (>5min)\n")
                return None

            # 查找下载的音频文件
            audio_path = None
            for ext in [".m4a", ".mp3", ".webm", ".opus", ".wav", ".aac"]:
                candidate = os.path.join(audio_dir, f"{bvid}{ext}")
                if os.path.exists(candidate):
                    audio_path = candidate
                    break
            if not audio_path:
                sys.stderr.write(f"[WARN] yt-dlp 未生成音频文件\n")
                return None
            sys.stderr.write(f"[INFO] 音频已下载: {audio_path} ({os.path.getsize(audio_path)/1024/1024:.1f} MB)\n")

            # ---- Step 2: Faster Whisper 转写 ----
            try:
                # 加载 NVIDIA CUDA DLL（Windows 下的 venv 修复）
                _nvidia_lib_dirs = [
                    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cublas", "bin"),
                    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cudnn", "bin"),
                    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cuda_nvrtc", "bin"),
                    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cuda_runtime", "bin"),
                ]
                for _d in _nvidia_lib_dirs:
                    if os.path.isdir(_d) and hasattr(os, "add_dll_directory"):
                        try:
                            os.add_dll_directory(_d)
                        except Exception:
                            pass
                        os.environ["PATH"] = _d + os.pathsep + os.environ.get("PATH", "")

                from faster_whisper import WhisperModel
            except ImportError:
                sys.stderr.write(f"[WARN] faster-whisper 未安装。pip install faster-whisper\n")
                return None

            model_name = options.get("model", "large-v3")
            device = options.get("device", "cuda")
            compute_type = options.get("compute_type", "float16")
            language = options.get("language", "zh")
            if language == "auto":
                language = None

            # 模型路径解析（优先本地 whisper_models 目录）
            model_path = model_name
            if not os.path.exists(model_path):
                local_model = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "whisper_models", model_name,
                )
                if os.path.exists(local_model):
                    model_path = local_model
                    sys.stderr.write(f"[INFO] 使用本地模型: {model_path}\n")

            sys.stderr.write(f"[INFO] 加载 Whisper 模型: {model_name} (device={device}, compute={compute_type})\n")
            try:
                model = WhisperModel(model_path, device=device, compute_type=compute_type)
            except Exception as e:
                # GPU 失败自动降级 CPU
                if device == "cuda":
                    sys.stderr.write(f"[WARN] CUDA 加载失败，降级 CPU + int8: {e}\n")
                    model = WhisperModel(model_path, device="cpu", compute_type="int8")
                else:
                    raise

            sys.stderr.write(f"[INFO] 开始 ASR 转写...\n")
            segments_iter, info = model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            segments = []
            full_text_parts = []
            for seg in segments_iter:
                text = seg.text.strip()
                if text:
                    segments.append({
                        "start": round(seg.start, 2),
                        "end": round(seg.end, 2),
                        "start_text": self._format_duration(int(seg.start * 1000)),
                        "end_text": self._format_duration(int(seg.end * 1000)),
                        "text": text,
                    })
                    full_text_parts.append(text)

            if not segments:
                sys.stderr.write(f"[WARN] ASR 转写结果为空\n")
                return None

            full_text = "\n".join(full_text_parts)
            sys.stderr.write(f"[INFO] ASR 完成: {len(segments)} 段 / {len(full_text)} 字\n")

            # 清理临时音频
            try:
                if not options.get("keep_audio"):
                    shutil.rmtree(audio_dir, ignore_errors=True)
            except Exception:
                pass

            return {
                "language": info.language if hasattr(info, "language") else "zh",
                "language_code": info.language if hasattr(info, "language") else "zh",
                "full_text": full_text,
                "segments": segments,
                "segment_count": len(segments),
                "_source": "whisper-asr",
                "_asr_model": model_name,
                "_audio_duration": round(info.duration, 1) if hasattr(info, "duration") else None,
            }
        except Exception as e:
            sys.stderr.write(f"[WARN] ASR 兜底失败: {e}\n")
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None

    def _find_ytdlp_exe(self):
        """跨平台寻找 yt-dlp 可执行文件"""
        skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(skill_dir, "venv", "Scripts", "yt-dlp.exe"),
            os.path.join(skill_dir, "venv", "bin", "yt-dlp"),
            os.path.join(skill_dir, "venv", "Scripts", "yt-dlp"),
            "yt-dlp",
        ]
        for c in candidates:
            if os.path.exists(c) or c == "yt-dlp":
                return c
        return None

    # ---- 评论提取 ----
    def get_comments(self, aid, count=50):
        """获取视频热门评论"""
        comments = []
        next_cursor = 0
        page = 0

        while len(comments) < count and page < 5:
            try:
                params = {
                    "type": 1,
                    "oid": aid,
                    "mode": 3,  # 热度排序
                    "next": next_cursor,
                    "ps": 20,
                }
                # 评论接口也可能需要签名
                params = self._sign_params(params)
                url = f"https://api.bilibili.com/x/v2/reply/main?{urlencode(params)}"

                data = http_get_json(url, headers=self.session_headers)
                if data.get("code") != 0:
                    break

                replies = data.get("data", {}).get("replies", [])
                if not replies:
                    break

                for reply in replies:
                    if len(comments) >= count:
                        break
                    content = reply.get("content", {})
                    member = reply.get("member", {})
                    comments.append({
                        "user": member.get("uname", ""),
                        "user_level": member.get("level_info", {}).get("current_level", 0),
                        "text": content.get("message", ""),
                        "likes": reply.get("like", 0),
                        "replies": reply.get("rcount", 0),
                        "time": time.strftime(
                            "%Y-%m-%d %H:%M",
                            time.localtime(reply.get("ctime", 0))
                        ),
                    })

                cursor = data.get("data", {}).get("cursor", {})
                next_cursor = cursor.get("next", 0)
                is_end = cursor.get("is_end", True)
                if is_end:
                    break
                page += 1
                time.sleep(0.3)  # 避免请求过快
            except Exception as e:
                sys.stderr.write(f"[WARN] 评论获取失败 (page {page}): {e}\n")
                break

        return comments

    # ---- B站搜索 ----
    def search(self, keyword, order="totalrank", page=1, page_size=20,
               duration=0, tids=0, category_id=None):
        """
        B站视频搜索

        参数:
            keyword:     搜索关键词
            order:       排序方式
                         - totalrank: 综合排序（默认）
                         - click: 最多播放
                         - pubdate: 最新发布
                         - dm: 最多弹幕
                         - stow: 最多收藏
            page:        页码（从1开始）
            page_size:   每页数量（最大50）
            duration:    时长筛选
                         - 0: 全部（默认）
                         - 1: 10分钟以下
                         - 2: 10-30分钟
                         - 3: 30-60分钟
                         - 4: 60分钟以上
            tids:        分区筛选（0为全部）
            category_id: 搜索分类（None为默认）

        返回:
            {
                "keyword": str,
                "total": int,          # 总结果数
                "page": int,
                "page_size": int,
                "results": [           # 视频列表
                    {
                        "bvid": str,
                        "aid": int,
                        "title": str,      # 已清理HTML标签
                        "author": str,
                        "author_mid": int,
                        "description": str,
                        "cover": str,
                        "duration": str,   # "mm:ss" 格式
                        "play": int,       # 播放量
                        "danmaku": int,    # 弹幕数
                        "favorites": int,  # 收藏数
                        "likes": int,      # 点赞数（搜索接口可能不返回）
                        "pub_date": str,   # 发布日期
                        "tag": str,        # 视频标签
                        "url": str,        # 完整视频链接
                    }
                ]
            }
        """
        params = {
            "search_type": "video",
            "keyword": keyword,
            "order": order,
            "page": page,
            "page_size": min(page_size, 50),
            "duration": duration,
        }
        if tids:
            params["tids"] = tids
        if category_id is not None:
            params["category_id"] = category_id

        params = self._sign_params(params)
        url_str = f"https://api.bilibili.com/x/web-interface/search/type?{urlencode(params)}"

        try:
            data = http_get_json(url_str, headers=self.session_headers)
            if data.get("code") != 0:
                return {"error": f"搜索失败: code={data.get('code')}, message={data.get('message','')}"}

            raw_results = data.get("data", {}).get("result", []) or []
            total = data.get("data", {}).get("numResults", 0)

            results = []
            for r in raw_results:
                # 清理标题中的 HTML 高亮标签
                title = r.get("title", "")
                title = re.sub(r'<em class="keyword">', "", title)
                title = re.sub(r"</em>", "", title)
                title = re.sub(r"<[^>]+>", "", title)

                # 清理描述
                desc = r.get("description", "")
                desc = re.sub(r"<[^>]+>", "", desc)

                # 解析时长字符串 "mm:ss"
                duration_str = r.get("duration", "0:00")

                # 发布日期
                pub_date = ""
                if r.get("pubdate"):
                    try:
                        pub_date = time.strftime("%Y-%m-%d", time.localtime(r["pubdate"]))
                    except (TypeError, ValueError, OSError):
                        pub_date = str(r.get("pubdate", ""))

                results.append({
                    "bvid": r.get("bvid", ""),
                    "aid": r.get("aid", 0),
                    "title": title.strip(),
                    "author": r.get("author", ""),
                    "author_mid": r.get("mid", 0),
                    "description": desc.strip(),
                    "cover": ("https:" + r["pic"]) if r.get("pic", "").startswith("//") else r.get("pic", ""),
                    "duration": duration_str,
                    "play": r.get("play", 0),
                    "danmaku": r.get("video_review", 0),  # B站搜索接口用 video_review 表示弹幕数
                    "favorites": r.get("favorites", 0),
                    "likes": r.get("like", 0),
                    "pub_date": pub_date,
                    "tag": r.get("tag", ""),
                    "url": f"https://www.bilibili.com/video/{r.get('bvid', '')}/",
                })

            return {
                "keyword": keyword,
                "total": total,
                "page": page,
                "page_size": page_size,
                "results": results,
            }

        except Exception as e:
            return {"error": f"搜索异常: {e}"}

    def search_all(self, keyword, order="totalrank", max_results=50,
                   duration=0, tids=0, page_delay=0.5):
        """
        搜索并自动翻页获取多页结果

        参数:
            keyword:      搜索关键词
            order:        排序方式（同 search 方法）
            max_results:  最大结果数（默认50）
            duration:     时长筛选（同 search 方法）
            tids:         分区筛选
            page_delay:   翻页间隔秒数（防止请求过快）

        返回: 同 search，但 results 包含多页汇总结果
        """
        all_results = []
        page = 1
        page_size = min(max_results, 50)
        total = None

        while len(all_results) < max_results:
            sys.stderr.write(f"[INFO] 搜索 \"{keyword}\" 第 {page} 页...\n")
            result = self.search(keyword, order=order, page=page,
                                 page_size=page_size, duration=duration, tids=tids)

            if "error" in result:
                if all_results:
                    break  # 已有部分结果，返回已获取的
                return result

            if total is None:
                total = result.get("total", 0)

            page_results = result.get("results", [])
            if not page_results:
                break

            all_results.extend(page_results)
            page += 1

            # 检查是否还有更多页
            if len(all_results) >= total or len(all_results) >= max_results:
                break

            time.sleep(page_delay)

        # 截取到 max_results
        all_results = all_results[:max_results]

        return {
            "keyword": keyword,
            "total": total or len(all_results),
            "page": 1,
            "page_size": len(all_results),
            "results": all_results,
        }

    # ---- 主入口 ----
    def extract(self, url, ytdlp_path="yt-dlp", cookie_file=None,
                enable_asr=False, asr_options=None):
        """提取B站视频的全部信息

        参数:
            enable_asr:  当 API + yt-dlp 全部失败时，是否启用 Whisper ASR 兜底
            asr_options: ASR 选项 dict，键见 _try_whisper_asr 文档
        """
        bvid = self.extract_bvid(url)
        if not bvid:
            return {"error": f"无法从链接中提取 BV 号: {url}"}

        result = {
            "platform": "bilibili",
            "url": url,
            "bvid": bvid,
            "video_info": None,
            "subtitles": None,
            "comments": [],
            "error": None,
        }

        # 获取视频信息
        sys.stderr.write(f"[INFO] 正在获取视频信息: {bvid}\n")
        info = self.get_video_info(bvid)
        if not info:
            result["error"] = "视频信息获取失败，可能视频不存在或已被删除"
            return result
        result["video_info"] = info

        # 获取字幕（先走 API 3 路 + yt-dlp，全部失败再走 ASR）
        sys.stderr.write(f"[INFO] 正在提取字幕...\n")
        aid = info["aid"]
        cid = info["cid"]
        bvid = info.get("bvid")
        # 第一次只走 API 三路（不开启 ASR，避免主分 P 失败就立刻 ASR）
        subtitles = self.get_subtitles(aid, cid, bvid=bvid, enable_asr=False)

        # 如果主分P没有字幕，尝试其他分P（仍走 API）
        if not subtitles and info.get("pages"):
            for page in info["pages"]:
                if page["cid"] != cid:
                    subtitles = self.get_subtitles(aid, page["cid"], bvid=bvid, enable_asr=False)
                    if subtitles:
                        break

        if subtitles:
            result["subtitles"] = subtitles
        else:
            # API 全失败 → yt-dlp 字幕路径
            sys.stderr.write("[INFO] API 未返回字幕，尝试使用 yt-dlp 获取...\n")
            subtitles = self._try_ytdlp_subtitles(url, ytdlp_path, cookie_file)
            if subtitles:
                result["subtitles"] = subtitles
            elif enable_asr:
                # 终极兜底：Whisper ASR
                sys.stderr.write("[INFO] yt-dlp 也未拿到字幕，启用 Whisper ASR 兜底...\n")
                asr_result = self._try_whisper_asr(bvid, asr_options or {})
                if asr_result:
                    result["subtitles"] = asr_result

        # 获取评论
        sys.stderr.write(f"[INFO] 正在获取热门评论...\n")
        result["comments"] = self.get_comments(aid, count=50)

        return result

    def _try_ytdlp_subtitles(self, url, ytdlp_path="yt-dlp", cookie_file=None):
        """尝试用 yt-dlp 提取字幕"""
        try:
            subprocess.run([ytdlp_path, "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            sys.stderr.write("[WARN] yt-dlp 不可用\n")
            return None

        try:
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                sub_file = os.path.join(tmpdir, "subtitle")
                cmd = [
                    ytdlp_path,
                    "--skip-download",
                    "--write-auto-subs",
                    "--write-subs",
                    "--sub-lang", "ai-zh,zh-CN,zh,zh-Hans",
                    "--sub-format", "json3/srv3/best",
                    "--convert-subs", "srt",
                    "-o", sub_file,
                ]
                # 添加 cookie 支持
                if cookie_file and os.path.exists(cookie_file):
                    cmd.extend(["--cookies", cookie_file])
                cmd.append(url)

                sys.stderr.write(f"[INFO] yt-dlp 正在下载字幕...\n")
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=60
                )

                # 寻找生成的字幕文件
                for f in os.listdir(tmpdir):
                    if f.endswith(".srt"):
                        srt_path = os.path.join(tmpdir, f)
                        with open(srt_path, "r", encoding="utf-8") as fp:
                            srt_text = fp.read()
                        result = self._parse_srt(srt_text)
                        if result:
                            sys.stderr.write(f"[INFO] 成功通过 yt-dlp 获取字幕 ({result['segment_count']} 段)\n")
                            return result

                sys.stderr.write(f"[WARN] yt-dlp 未能下载字幕\n")

        except Exception as e:
            sys.stderr.write(f"[WARN] yt-dlp 字幕提取失败: {e}\n")
        return None

    @staticmethod
    def _parse_srt(srt_text):
        """解析 SRT 字幕文本"""
        segments = []
        full_text_parts = []
        blocks = srt_text.strip().split("\n\n")

        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) >= 3:
                text = " ".join(lines[2:]).strip()
                # 去除 HTML 标签
                text = re.sub(r"<[^>]+>", "", text)
                if text and text not in full_text_parts:  # 去重
                    full_text_parts.append(text)
                    segments.append({
                        "start": 0,
                        "end": 0,
                        "start_text": "",
                        "end_text": "",
                        "text": text,
                    })

        if segments:
            return {
                "language": "中文",
                "language_code": "zh",
                "full_text": "\n".join(full_text_parts),
                "segments": segments,
                "segment_count": len(segments),
            }
        return None


# ============================================================
# 主入口
# ============================================================

def load_cookie_string(cookie_file):
    """从 Netscape cookie 文件中读取 B站 cookie 并返回为 header 字符串"""
    if not cookie_file or not os.path.exists(cookie_file):
        return None
    try:
        cookies = []
        with open(cookie_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 7:
                    domain = parts[0]
                    name = parts[5]
                    value = parts[6]
                    if "bilibili" in domain or "bilivideo" in domain:
                        cookies.append(f"{name}={value}")
        if cookies:
            return "; ".join(cookies)
    except Exception as e:
        sys.stderr.write(f"[WARN] Cookie 文件读取失败: {e}\n")
    return None


# 默认 cookie 文件路径
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_COOKIE_FILE = os.path.join(SKILL_DIR, "cookies.txt")
DEFAULT_YTDLP = os.path.join(SKILL_DIR, "venv", "bin", "yt-dlp")


def main():
    # ---- 旧用法兼容：如果第一个非 flag 参数像 URL，自动插入 "extract" ----
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if first_arg not in ("extract", "search", "-h", "--help") and \
           (first_arg.startswith("http") or first_arg.startswith("BV")):
            sys.argv.insert(1, "extract")

    parser = argparse.ArgumentParser(
        description="视频内容提取工具 - 支持 B站搜索、视频提取和总结"
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # --- extract 子命令 ---
    extract_parser = subparsers.add_parser("extract", help="提取视频内容（字幕、评论、信息）")
    extract_parser.add_argument("url", help="B站视频链接")
    extract_parser.add_argument("--output-dir", default="/tmp/video_summary", help="输出目录")
    extract_parser.add_argument("--cookies", default=DEFAULT_COOKIE_FILE, help="Cookie 文件路径")
    extract_parser.add_argument("--yt-dlp", default=None, help="yt-dlp 可执行文件路径")
    extract_parser.add_argument("--no-comments", action="store_true", help="不获取评论")
    extract_parser.add_argument("--no-subtitles", action="store_true", help="不获取字幕")
    extract_parser.add_argument("--comment-count", type=int, default=50, help="评论获取数量")
    # ---- ASR 兜底（B 站 API + yt-dlp 全部失败时启用 Faster Whisper 本地转写）----
    extract_parser.add_argument("--enable-asr", action="store_true",
                                help="字幕全部 API+yt-dlp 失败时，启用 Whisper ASR 本地转写（需 yt-dlp + faster-whisper）")
    extract_parser.add_argument("--asr-model", default="large-v3",
                                help="Whisper 模型（默认 large-v3，无 GPU 推荐 medium）")
    extract_parser.add_argument("--asr-device", default="cuda", choices=["cuda", "cpu"],
                                help="ASR 计算设备（默认 cuda，自动失败降级 cpu）")
    extract_parser.add_argument("--asr-compute-type", default="float16",
                                choices=["float16", "int8", "float32"],
                                help="ASR 计算精度（默认 float16；CPU 推荐 int8）")
    extract_parser.add_argument("--asr-language", default="zh",
                                help="ASR 识别语言（默认 zh，auto 为自动检测）")

    # --- search 子命令 ---
    search_parser = subparsers.add_parser("search", help="B站视频搜索")
    search_parser.add_argument("keyword", help="搜索关键词")
    search_parser.add_argument("--order", default="totalrank",
                               choices=["totalrank", "click", "pubdate", "dm", "stow"],
                               help="排序方式: totalrank(综合) click(播放量) pubdate(最新) dm(弹幕) stow(收藏)")
    search_parser.add_argument("--max-results", type=int, default=20, help="最大结果数（默认20）")
    search_parser.add_argument("--duration", type=int, default=0, choices=[0, 1, 2, 3, 4],
                               help="时长筛选: 0(全部) 1(<10分钟) 2(10-30分钟) 3(30-60分钟) 4(>60分钟)")
    search_parser.add_argument("--tids", type=int, default=0, help="分区ID筛选（0为全部）")
    search_parser.add_argument("--cookies", default=DEFAULT_COOKIE_FILE, help="Cookie 文件路径")
    search_parser.add_argument("--page-delay", type=float, default=0.5, help="翻页间隔秒数")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # 通用 Cookie 加载
    cookie_str = load_cookie_string(args.cookies)
    if cookie_str:
        sys.stderr.write(f"[INFO] 已加载 Cookie 文件: {args.cookies}\n")
    else:
        sys.stderr.write(f"[INFO] 未找到 Cookie 文件，部分功能（如B站字幕）可能受限\n")

    if args.command == "search":
        # ---- B站搜索 ----
        extractor = BilibiliExtractor(cookie_str=cookie_str)
        result = extractor.search_all(
            keyword=args.keyword,
            order=args.order,
            max_results=args.max_results,
            duration=args.duration,
            tids=args.tids,
            page_delay=args.page_delay,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "extract":
        # ---- 视频提取 ----
        ytdlp_path = args.yt_dlp
        if not ytdlp_path:
            if os.path.exists(DEFAULT_YTDLP):
                ytdlp_path = DEFAULT_YTDLP
            else:
                ytdlp_path = "yt-dlp"

        url = args.url.strip()
        platform = detect_platform(url)

        if platform == "bilibili":
            extractor = BilibiliExtractor(cookie_str=cookie_str)
            asr_options = {
                "model": args.asr_model,
                "device": args.asr_device,
                "compute_type": args.asr_compute_type,
                "language": args.asr_language,
            }
            result = extractor.extract(
                url,
                ytdlp_path=ytdlp_path,
                cookie_file=args.cookies,
                enable_asr=args.enable_asr,
                asr_options=asr_options,
            )
        else:
            result = {"error": f"不支持的平台: {url}\n支持的平台: bilibili"}

        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
