"""
B站视频ASR语音识别脚本（Faster Whisper 本地版）
功能：使用本地Faster Whisper模型对B站视频音频进行语音转文字

用法：
  # 对单个音频文件进行ASR
  python asr_bilibili.py --audio ./audio/BV1xx.m4a --title "视频标题" --collection "合集名" --output ./subtitles

  # 批量ASR（通过JSON配置文件）
  python asr_bilibili.py --config videos.json --audio-dir ./audio --output ./subtitles

  # 指定模型和设备
  python asr_bilibili.py --audio ./audio/BV1xx.m4a --title "标题" --model large-v3 --device cuda --compute-type float16

  videos.json 格式：
  [
    {"bvid": "BV1xx", "title": "视频标题", "collection": "合集名"},
    ...
  ]

依赖：pip install faster-whisper
可选：NVIDIA GPU + CUDA（大幅加速）
"""

import os
import sys
import json
import time
import argparse

# 添加NVIDIA CUDA DLL搜索路径（Windows下pip安装的CUDA库不在系统PATH中）
_nvidia_lib_dirs = [
    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cublas", "bin"),
    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cudnn", "bin"),
    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cuda_nvrtc", "bin"),
    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cuda_runtime", "bin"),
]
for _d in _nvidia_lib_dirs:
    if os.path.isdir(_d):
        os.add_dll_directory(_d)
        os.environ["PATH"] = _d + os.pathsep + os.environ.get("PATH", "")

# 修复Windows下重定向输出的编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def find_audio_file(bvid, audio_dir):
    """查找已下载的音频文件（支持多种格式）"""
    for ext in ['.m4a', '.mp3', '.webm', '.opus', '.wav', '.aac', '.flac']:
        candidate = os.path.join(audio_dir, f"{bvid}{ext}")
        if os.path.exists(candidate):
            file_size = os.path.getsize(candidate)
            print(f"  找到音频文件: {candidate} ({file_size / 1024 / 1024:.1f} MB)")
            return candidate
    return None


def transcribe_with_faster_whisper(audio_path, model, language="zh", model_name="large-v3", device="cuda"):
    """
    使用Faster Whisper进行本地语音识别

    返回: (纯文本, 带时间戳的句子列表)
    """
    file_size = os.path.getsize(audio_path)
    print(f"  音频文件: {os.path.basename(audio_path)} ({file_size / 1024 / 1024:.1f} MB)")
    print(f"  开始语音识别（模型: {model_name}, 设备: {device}）...")

    start_time = time.time()

    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    print(f"  检测到语言: {info.language} (置信度: {info.language_probability:.2%})")
    print(f"  音频时长: {info.duration:.1f} 秒 ({info.duration / 60:.1f} 分钟)")

    texts = []
    sentences = []
    segment_count = 0

    for segment in segments:
        segment_count += 1
        text = segment.text.strip()
        texts.append(text)
        sentences.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": text,
        })

        if segment_count % 50 == 0:
            progress_pct = segment.end / info.duration * 100 if info.duration > 0 else 0
            print(f"  进度: {segment_count} 段, {segment.end:.0f}s / {info.duration:.0f}s ({progress_pct:.0f}%)")

    elapsed = time.time() - start_time
    speed_ratio = info.duration / elapsed if elapsed > 0 else 0

    full_text = '\n'.join(texts)
    print(f"  ✅ 识别完成! 共 {segment_count} 段, {len(full_text)} 字")
    print(f"  耗时: {elapsed:.1f} 秒 (速度: {speed_ratio:.1f}x 实时)")

    return full_text, sentences


def format_srt_time(seconds):
    """将秒数转换为SRT时间格式 HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def save_subtitle(text, sentences, title, collection, output_dir):
    """保存字幕文本到对应的合集目录"""
    collection_dir = os.path.join(output_dir, collection) if collection else output_dir
    os.makedirs(collection_dir, exist_ok=True)

    # 清理文件名中的非法字符
    safe_title = title
    for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        safe_title = safe_title.replace(ch, '_')

    # 保存纯文本版本
    txt_path = os.path.join(collection_dir, f"{safe_title}.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  ✅ 纯文本字幕已保存: {txt_path}")

    # 保存带时间戳的JSON版本
    json_path = os.path.join(collection_dir, f"{safe_title}_timestamps.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(sentences, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 时间戳字幕已保存: {json_path}")

    # 保存SRT格式字幕
    srt_path = os.path.join(collection_dir, f"{safe_title}.srt")
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, s in enumerate(sentences, 1):
            start_ts = format_srt_time(s["start"])
            end_ts = format_srt_time(s["end"])
            f.write(f"{i}\n{start_ts} --> {end_ts}\n{s['text']}\n\n")
    print(f"  ✅ SRT字幕已保存: {srt_path}")

    print(f"  字幕总字数: {len(text)}")
    return txt_path


def main():
    parser = argparse.ArgumentParser(description='B站视频ASR语音识别（Faster Whisper 本地版）')

    # 单文件模式
    parser.add_argument('--audio', type=str, help='单个音频文件路径')
    parser.add_argument('--title', type=str, default='未命名视频', help='视频标题')
    parser.add_argument('--collection', type=str, default='', help='所属合集名称')

    # 批量模式
    parser.add_argument('--config', type=str,
                        help='批量配置JSON文件路径（包含bvid/title/collection列表）')
    parser.add_argument('--audio-dir', type=str, default='./bilibili_audio_temp',
                        help='音频文件目录（批量模式，默认: ./bilibili_audio_temp）')

    # 模型配置
    parser.add_argument('--model', type=str, default='large-v3',
                        help='Whisper模型名称或本地路径（默认: large-v3）')
    parser.add_argument('--device', type=str, default='cuda',
                        choices=['cuda', 'cpu'], help='计算设备（默认: cuda）')
    parser.add_argument('--compute-type', type=str, default='float16',
                        choices=['float16', 'int8', 'float32'],
                        help='计算精度（默认: float16）')
    parser.add_argument('--language', type=str, default='zh',
                        help='识别语言（默认: zh，设为auto自动检测）')

    # 输出
    parser.add_argument('--output', type=str, default='./bilibili_subtitles',
                        help='输出目录（默认: ./bilibili_subtitles）')

    args = parser.parse_args()

    if args.language == 'auto':
        args.language = None

    # 确定模型路径
    model_path = args.model
    # 如果是模型名称（非路径），检查本地是否有下载好的模型
    if not os.path.exists(model_path):
        local_model = os.path.join(os.getcwd(), 'whisper_models', model_path)
        if os.path.exists(local_model):
            model_path = local_model
            print(f"使用本地模型: {model_path}")

    os.makedirs(args.output, exist_ok=True)

    # 构建视频列表
    videos = []
    if args.audio:
        # 单文件模式
        videos.append({
            'audio_path': args.audio,
            'title': args.title,
            'collection': args.collection,
        })
    elif args.config:
        # 批量模式
        with open(args.config, 'r', encoding='utf-8') as f:
            video_list = json.load(f)
        for v in video_list:
            audio_path = find_audio_file(v['bvid'], args.audio_dir)
            if audio_path:
                videos.append({
                    'audio_path': audio_path,
                    'title': v.get('title', v['bvid']),
                    'collection': v.get('collection', ''),
                })
            else:
                print(f"⚠️ 未找到 {v['bvid']} 的音频文件，跳过")
    else:
        parser.print_help()
        return

    if not videos:
        print("没有可处理的视频")
        return

    print("=" * 60)
    print("B站视频ASR语音识别（Faster Whisper 本地版）")
    print(f"模型: {model_path} | 设备: {args.device} | 精度: {args.compute_type}")
    print(f"待处理: {len(videos)} 个视频")
    print("=" * 60)

    # 加载模型
    print(f"\n正在加载Whisper模型...")
    from faster_whisper import WhisperModel

    load_start = time.time()
    model = WhisperModel(model_path, device=args.device, compute_type=args.compute_type)
    load_time = time.time() - load_start
    print(f"✅ 模型加载完成! 耗时: {load_time:.1f} 秒\n")

    # 逐个处理
    results = []
    for video in videos:
        audio_path = video['audio_path']
        title = video['title']
        collection = video['collection']

        print(f"\n{'=' * 60}")
        print(f"处理: {title}")
        print(f"音频: {audio_path}")
        print(f"{'=' * 60}")

        try:
            text, sentences = transcribe_with_faster_whisper(
                audio_path, model,
                language=args.language,
                model_name=args.model,
                device=args.device,
            )

            if text:
                filepath = save_subtitle(text, sentences, title, collection, args.output)
                results.append({
                    "title": title,
                    "status": "success",
                    "filepath": filepath,
                    "char_count": len(text),
                    "segment_count": len(sentences),
                })
            else:
                print(f"  ❌ 语音识别结果为空")
                results.append({"title": title, "status": "empty_result"})

        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            results.append({"title": title, "status": "error", "error": str(e)})

    # 输出总结
    print(f"\n\n{'=' * 60}")
    print("处理结果总结:")
    print(f"{'=' * 60}")
    for r in results:
        status_icon = {"success": "✅", "empty_result": "⚠️", "error": "💥"}.get(r["status"], "?")
        print(f"  {status_icon} {r['title']}")
        if "filepath" in r:
            print(f"     文件: {r['filepath']}")
        if "char_count" in r:
            print(f"     字数: {r['char_count']}, 片段: {r.get('segment_count', 0)}")
        if "error" in r:
            print(f"     错误: {r['error']}")


if __name__ == "__main__":
    main()
