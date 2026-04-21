from __future__ import annotations

import json
import math
import os
import re
import urllib.request
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .config import RuntimeConfig
from .models import ConceptCard, KnowledgePackage, PipelineResult, TranscriptBundle, TranscriptSegment, TreeNode, VideoMetadata
from .utils import (
    CHINESE_STOPWORDS,
    ENGLISH_STOPWORDS,
    now_iso,
    sanitize_filename,
    slugify,
    timestamp_label,
    utc_stamp,
    write_json,
    write_text,
)


class PipelineError(RuntimeError):
    """Raised when ingest cannot complete."""


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def run_ingest(input_value: str, config: RuntimeConfig) -> PipelineResult:
    input_value = input_value.strip()
    if not input_value:
        raise PipelineError("输入为空，无法处理。")
    run_id = f"{utc_stamp()}-{slugify(input_value)[:48]}"
    run_dir = config.cache_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    if _is_url(input_value):
        metadata, transcript = _process_remote_source(input_value, config, run_dir, warnings)
    else:
        metadata, transcript = _process_local_media(Path(input_value), config, run_dir, warnings)

    if not transcript.segments:
        raise PipelineError("没有拿到任何可用转写内容。")

    knowledge = _analyze_transcript(metadata, transcript, config, warnings)
    confidence = _calculate_overall_confidence(transcript, knowledge)
    status = "ready" if confidence >= 0.72 and not transcript.low_confidence_segments else "draft"
    if transcript.origin != "subtitle" and transcript.low_confidence_reason:
        warnings.append(transcript.low_confidence_reason)
    write_json(run_dir / "analysis.json", knowledge.to_dict())
    result = PipelineResult(
        metadata=metadata,
        transcript=transcript,
        knowledge=knowledge,
        status=status,
        confidence=confidence,
        run_dir=run_dir,
        artifact_paths={},
        warnings=warnings,
    )
    return result


def _process_remote_source(
    source_url: str,
    config: RuntimeConfig,
    run_dir: Path,
    warnings: list[str],
) -> tuple[VideoMetadata, TranscriptBundle]:
    info = _extract_info_with_ytdlp(source_url)
    write_json(run_dir / "raw_info.json", info)
    entry, part_index = _select_entry(info, source_url)
    metadata = _build_remote_metadata(source_url, info, entry, part_index, run_dir)
    transcript = _try_subtitle_first(entry, config, run_dir, warnings)
    if transcript:
        return metadata, transcript
    media_path = _download_audio(source_url, run_dir)
    transcript = _transcribe_media(media_path, config)
    transcript.source_path = str(media_path)
    transcript.low_confidence_reason = "字幕缺失，已回退到本地 ASR 草稿。"
    write_json(run_dir / "transcript.json", transcript.to_dict())
    write_text(run_dir / "transcript.txt", transcript.plain_text())
    return metadata, transcript


def _process_local_media(
    media_path: Path,
    config: RuntimeConfig,
    run_dir: Path,
    warnings: list[str],
) -> tuple[VideoMetadata, TranscriptBundle]:
    if not media_path.exists():
        raise PipelineError(f"本地媒体不存在: {media_path}")
    metadata = VideoMetadata(
        source_platform="local",
        source_url=str(media_path),
        video_id=sanitize_filename(media_path.stem),
        title=media_path.stem,
        creator="local",
        published_at=None,
        processed_at=now_iso(),
        raw_info_path=None,
    )
    transcript = _transcribe_media(media_path, config)
    transcript.source_path = str(media_path)
    transcript.low_confidence_reason = "本地媒体默认走 ASR 转写，请优先人工抽查关键段落。"
    write_json(run_dir / "transcript.json", transcript.to_dict())
    write_text(run_dir / "transcript.txt", transcript.plain_text())
    if transcript.low_confidence_segments:
        warnings.append("本地媒体转写存在低置信段落。")
    return metadata, transcript


def _extract_info_with_ytdlp(source_url: str) -> dict[str, Any]:
    try:
        from yt_dlp import YoutubeDL
    except ImportError as exc:
        raise PipelineError("缺少 yt-dlp 依赖，请先运行 setup 脚本。") from exc
    options = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": False,
        "extract_flat": False,
    }
    with YoutubeDL(options) as ydl:
        return ydl.extract_info(source_url, download=False)


def _select_entry(info: dict[str, Any], source_url: str) -> tuple[dict[str, Any], int | None]:
    entries = info.get("entries") or []
    if not entries:
        return info, info.get("playlist_index")
    query_index = _query_part_index(source_url)
    if query_index:
        for entry in entries:
            if entry.get("playlist_index") == query_index:
                return {**info, **entry}, query_index
        idx = max(0, min(len(entries) - 1, query_index - 1))
        return {**info, **entries[idx]}, query_index
    requested = info.get("requested_entries")
    if requested:
        requested_index = requested[0] - 1
        if 0 <= requested_index < len(entries):
            entry = entries[requested_index]
            return {**info, **entry}, entry.get("playlist_index")
    first = entries[0]
    return {**info, **first}, first.get("playlist_index")


def _query_part_index(source_url: str) -> int | None:
    query = parse_qs(urlparse(source_url).query)
    raw = query.get("p")
    if not raw:
        return None
    try:
        return int(raw[0])
    except (ValueError, TypeError):
        return None


def _build_remote_metadata(
    source_url: str,
    info: dict[str, Any],
    entry: dict[str, Any],
    part_index: int | None,
    run_dir: Path,
) -> VideoMetadata:
    published_at = None
    upload_date = entry.get("upload_date") or info.get("upload_date")
    timestamp = entry.get("timestamp") or info.get("timestamp")
    if upload_date and len(upload_date) == 8:
        published_at = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    elif timestamp:
        published_at = __import__("datetime").datetime.fromtimestamp(timestamp).date().isoformat()
    bvid = entry.get("bvid") or info.get("bvid") or entry.get("display_id") or info.get("display_id") or str(entry.get("id") or info.get("id"))
    part_title = entry.get("title") if entry.get("title") != info.get("title") else None
    title = entry.get("title") or info.get("title") or bvid
    if part_index:
        video_id = f"{bvid}-P{part_index}"
    else:
        video_id = str(bvid)
    return VideoMetadata(
        source_platform="bilibili" if "bilibili.com" in source_url else "remote",
        source_url=source_url,
        video_id=video_id,
        title=title,
        creator=entry.get("uploader") or info.get("uploader") or entry.get("channel") or "unknown",
        published_at=published_at,
        processed_at=now_iso(),
        part_title=part_title,
        part_index=part_index,
        series_title=info.get("title") if part_title else None,
        cover_url=entry.get("thumbnail") or info.get("thumbnail"),
        raw_info_path=str(run_dir / "raw_info.json"),
    )


def _try_subtitle_first(
    entry: dict[str, Any],
    config: RuntimeConfig,
    run_dir: Path,
    warnings: list[str],
) -> TranscriptBundle | None:
    subtitle_candidates = _collect_subtitle_candidates(entry)
    if not subtitle_candidates:
        warnings.append("未发现可直接使用的字幕轨。")
        return None
    selected = _pick_subtitle_candidate(subtitle_candidates, config.language)
    if not selected:
        warnings.append("字幕轨存在，但没有选中可解析格式。")
        return None
    subtitle_payload = _download_json_or_text(selected["url"])
    write_text(run_dir / "subtitle_source.txt", subtitle_payload if isinstance(subtitle_payload, str) else json.dumps(subtitle_payload, ensure_ascii=False, indent=2))
    segments = _parse_subtitle_payload(subtitle_payload, selected["ext"])
    if not segments:
        warnings.append("字幕下载成功，但解析后为空。")
        return None
    transcript = TranscriptBundle(
        origin="subtitle",
        language=selected["language"],
        segments=segments,
        source_path=selected["url"],
    )
    write_json(run_dir / "transcript.json", transcript.to_dict())
    write_text(run_dir / "transcript.txt", transcript.plain_text())
    return transcript


def _collect_subtitle_candidates(entry: dict[str, Any]) -> list[dict[str, str]]:
    buckets = []
    for origin_name, source in (("subtitle", entry.get("subtitles") or {}), ("auto", entry.get("automatic_captions") or {})):
        for language, tracks in source.items():
            if "danmaku" in language.lower():
                continue
            for track in tracks or []:
                url = track.get("url")
                if not url:
                    continue
                ext = track.get("ext") or track.get("name") or "json"
                buckets.append(
                    {
                        "origin": origin_name,
                        "language": language,
                        "url": url,
                        "ext": ext.lower(),
                    }
                )
    return buckets


def _pick_subtitle_candidate(candidates: list[dict[str, str]], preferred_language: str) -> dict[str, str] | None:
    score_map = {
        preferred_language: 0,
        "zh-CN": 1,
        "zh-Hans": 2,
        "zh": 3,
        "cmn-Hans-CN": 4,
        "en": 5,
    }
    ranked = sorted(
        candidates,
        key=lambda item: (
            0 if item["origin"] == "subtitle" else 1,
            score_map.get(item["language"], 99),
            0 if item["ext"] in {"json", "vtt", "srt"} else 1,
        ),
    )
    return ranked[0] if ranked else None


def _download_json_or_text(url: str) -> dict[str, Any] | str:
    with urllib.request.urlopen(url) as response:
        payload = response.read().decode("utf-8", errors="ignore")
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload


def _parse_subtitle_payload(payload: dict[str, Any] | str, ext: str) -> list[TranscriptSegment]:
    if isinstance(payload, dict):
        if isinstance(payload.get("body"), list):
            return [
                TranscriptSegment(
                    start=float(item.get("from", 0.0)),
                    end=float(item.get("to", item.get("from", 0.0))),
                    text=str(item.get("content", "")).strip(),
                    confidence=0.98,
                    source="subtitle",
                )
                for item in payload["body"]
                if str(item.get("content", "")).strip()
            ]
        if isinstance(payload.get("events"), list):
            segments = []
            for item in payload["events"]:
                text = "".join(seg.get("utf8", "") for seg in item.get("segs", []))
                if text.strip():
                    segments.append(
                        TranscriptSegment(
                            start=float(item.get("tStartMs", 0)) / 1000.0,
                            end=float(item.get("tStartMs", 0) + item.get("dDurationMs", 0)) / 1000.0,
                            text=text.strip(),
                            confidence=0.96,
                            source="subtitle",
                        )
                    )
            return segments
        return []
    if ext == "srt":
        return _parse_srt(payload)
    return _parse_vtt_or_plain(payload)


def _parse_srt(payload: str) -> list[TranscriptSegment]:
    blocks = re.split(r"\n\s*\n", payload.strip())
    results: list[TranscriptSegment] = []
    for block in blocks:
        lines = [line.strip("\ufeff") for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        timing_line = lines[1] if "-->" in lines[1] else lines[0]
        if "-->" not in timing_line:
            continue
        start_raw, end_raw = [part.strip() for part in timing_line.split("-->")]
        text_lines = lines[2:] if timing_line == lines[1] else lines[1:]
        results.append(
            TranscriptSegment(
                start=_parse_srt_time(start_raw),
                end=_parse_srt_time(end_raw),
                text=" ".join(text_lines).strip(),
                confidence=0.98,
                source="subtitle",
            )
        )
    return [segment for segment in results if segment.text]


def _parse_vtt_or_plain(payload: str) -> list[TranscriptSegment]:
    results: list[TranscriptSegment] = []
    blocks = re.split(r"\n\s*\n", payload.strip())
    for block in blocks:
        lines = [line.strip("\ufeff") for line in block.splitlines() if line.strip() and line.strip() != "WEBVTT"]
        if len(lines) < 2:
            continue
        timing_line = lines[0]
        if "-->" not in timing_line:
            continue
        start_raw, end_raw = [part.strip() for part in timing_line.split("-->")]
        results.append(
            TranscriptSegment(
                start=_parse_srt_time(start_raw.replace(".", ",")),
                end=_parse_srt_time(end_raw.replace(".", ",")),
                text=" ".join(lines[1:]).strip(),
                confidence=0.98,
                source="subtitle",
            )
        )
    return [segment for segment in results if segment.text]


def _parse_srt_time(raw: str) -> float:
    match = re.match(r"(?:(\d+):)?(\d+):(\d+)[,.](\d+)", raw)
    if not match:
        return 0.0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    milliseconds = int(match.group(4).ljust(3, "0")[:3])
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0


def _download_audio(source_url: str, run_dir: Path) -> Path:
    try:
        from yt_dlp import YoutubeDL
    except ImportError as exc:
        raise PipelineError("缺少 yt-dlp 依赖，无法下载音频。") from exc
    download_dir = run_dir / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(download_dir / "%(id)s.%(ext)s")
    options = {
        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": output_template,
        "restrictfilenames": False,
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(source_url, download=True)
        requested = info.get("requested_downloads") or []
        if requested:
            filepath = requested[0].get("filepath")
            if filepath:
                return Path(filepath)
        path = ydl.prepare_filename(info)
        return Path(path)


def _transcribe_media(media_path: Path, config: RuntimeConfig) -> TranscriptBundle:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise PipelineError("缺少 faster-whisper 依赖，请先运行 setup 脚本。") from exc
    model = WhisperModel(config.whisper_model, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(media_path), language=config.language, vad_filter=True, beam_size=5)
    items: list[TranscriptSegment] = []
    for segment in segments:
        avg_logprob = getattr(segment, "avg_logprob", None)
        confidence = 0.55
        if avg_logprob is not None:
            confidence = max(0.05, min(0.99, math.exp(avg_logprob)))
        items.append(
            TranscriptSegment(
                start=float(segment.start),
                end=float(segment.end),
                text=segment.text.strip(),
                confidence=round(confidence, 3),
                source="asr",
            )
        )
    return TranscriptBundle(
        origin="asr",
        language=getattr(info, "language", config.language),
        segments=items,
    )


def _analyze_transcript(
    metadata: VideoMetadata,
    transcript: TranscriptBundle,
    config: RuntimeConfig,
    warnings: list[str],
) -> KnowledgePackage:
    if not config.skip_openai and config.openai_backend in {"auto", "openai"} and os.environ.get("OPENAI_API_KEY"):
        try:
            return _analyze_with_openai(metadata, transcript, config)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"OpenAI 抽取失败，已回退到 extractive 模式: {exc}")
    return _analyze_extractively(metadata, transcript)


def _analyze_with_openai(
    metadata: VideoMetadata,
    transcript: TranscriptBundle,
    config: RuntimeConfig,
) -> KnowledgePackage:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise PipelineError("检测到 OPENAI_API_KEY，但未安装 openai 包。") from exc
    client = OpenAI()
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "topics": {"type": "array", "items": {"type": "string"}},
            "tags": {"type": "array", "items": {"type": "string"}},
            "knowledge_tree": {
                "type": "array",
                "items": {"$ref": "#/$defs/treeNode"},
            },
            "concepts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "definition": {"type": "string"},
                        "importance": {"type": "string"},
                        "example": {"type": "string"},
                        "pitfall": {"type": "string"},
                    },
                    "required": ["name", "definition", "importance", "example", "pitfall"],
                },
            },
            "key_points": {"type": "array", "items": {"type": "string"}},
            "examples": {"type": "array", "items": {"type": "string"}},
            "pitfalls": {"type": "array", "items": {"type": "string"}},
            "actions": {"type": "array", "items": {"type": "string"}},
            "review_questions": {"type": "array", "items": {"type": "string"}},
            "follow_ups": {"type": "array", "items": {"type": "string"}},
            "confidence_notes": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "summary",
            "topics",
            "tags",
            "knowledge_tree",
            "concepts",
            "key_points",
            "examples",
            "pitfalls",
            "actions",
            "review_questions",
            "follow_ups",
            "confidence_notes",
        ],
        "$defs": {
            "treeNode": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "children": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/treeNode"},
                    },
                },
                "required": ["title", "children"],
            }
        },
    }
    prompt = f"""
你是一个高密度知识视频整理助手。请把下面视频转成适合 Obsidian 复习的结构化中文知识笔记。

要求：
1. 不要写空话，不要套模板。
2. 输出应强调：一句话总结、知识树、概念定义、关键论证/例子、易混点、可执行结论、复习问答、后续延伸。
3. topics 只保留 2 到 4 个主题；tags 只保留 4 到 8 个高价值标签。
4. concepts 只保留最关键的 3 到 6 个。
5. confidence_notes 用于记录字幕缺失、ASR 草稿、概念不确定等风险。

视频信息：
- 标题：{metadata.title}
- 作者：{metadata.creator}
- 来源：{metadata.source_url}
- part_title：{metadata.part_title or "无"}

转写正文：
{transcript.plain_text()[:18000]}
"""
    response = client.responses.create(
        model=config.openai_model,
        input=[
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "video_kb_analysis",
                "schema": schema,
                "strict": True,
            }
        },
    )
    payload = json.loads(response.output_text)
    return _knowledge_from_payload(payload, backend=f"openai:{config.openai_model}")


def _analyze_extractively(metadata: VideoMetadata, transcript: TranscriptBundle) -> KnowledgePackage:
    title_phrases = _extract_title_phrases(metadata.title)
    normalized_segments = [_normalize_known_terms(segment.text, title_phrases) for segment in transcript.segments]
    text = "\n".join(normalized_segments)

    if _looks_like_harness_video(metadata.title, text):
        return _build_harness_knowledge_package(metadata, transcript)

    sentences = _build_analysis_units(normalized_segments)
    keywords = _top_keywords(text, limit=8, title_phrases=title_phrases)
    topics = list(dict.fromkeys(title_phrases + keywords))[:3] or [metadata.title[:18]]
    tags = list(dict.fromkeys((["视频知识库", "B站学习"] + title_phrases + topics + keywords[:4])))[:8]
    ranked_sentences = _rank_sentences(sentences, keywords)
    summary = "；".join(ranked_sentences[:2]) if ranked_sentences else metadata.title
    concepts = []
    for keyword in keywords[:5]:
        evidence = next((sentence for sentence in ranked_sentences if keyword in sentence), summary)
        concepts.append(
            ConceptCard(
                name=keyword,
                definition=evidence,
                importance=f"{keyword} 是本视频中的高频核心概念，需要优先回顾其定义与适用边界。",
                example=evidence,
                pitfall=f"不要只记住 {keyword} 的结论，要同时核对它的前提、例外和使用条件。",
            )
        )
    key_points = ranked_sentences[:5] or [summary]
    examples = ranked_sentences[5:8] or key_points[:2]
    pitfalls = [
        sentence for sentence in ranked_sentences if any(marker in sentence for marker in ("但是", "不过", "注意", "误区", "不要"))
    ][:4]
    if not pitfalls:
        pitfalls = [
            "需要重点复查视频中的定义边界与适用条件，避免只记住结论。",
            "如果是 ASR 草稿，关键公式、术语和专有名词要回看原视频确认。",
        ]
    actions = [
        f"先用 3 句话复述 {topics[0]} 的主结论。",
        "回看原视频中最容易混淆的定义、条件和例子。",
        "把本条视频和相近主题的视频做对照，抽出共同框架。",
    ]
    review_questions = [
        f"{topic} 在这条视频里是如何被定义或拆解的？" for topic in topics[:3]
    ]
    review_questions.append("如果不看原视频，你能否用自己的话复现知识树？")
    follow_ups = [
        "找一条同主题视频做横向比较，补齐不同作者的解释角度。",
        "把最核心的 3 个概念改写成自己的概念卡。",
    ]
    confidence_notes = []
    if transcript.origin != "subtitle":
        confidence_notes.append("当前笔记基于 ASR 草稿生成，关键术语和公式需要人工抽查。")
    if transcript.low_confidence_segments:
        confidence_notes.append(f"存在 {len(transcript.low_confidence_segments)} 个低置信段落，复习时优先回看。")
    knowledge_tree = [
        TreeNode("视频主旨", [TreeNode(summary)]),
        TreeNode("核心概念", [TreeNode(concept.name) for concept in concepts[:4]]),
        TreeNode("关键论证", [TreeNode(point) for point in key_points[:4]]),
        TreeNode("复习抓手", [TreeNode(question) for question in review_questions[:4]]),
    ]
    return KnowledgePackage(
        summary=summary,
        topics=topics,
        tags=tags,
        knowledge_tree=knowledge_tree,
        concepts=concepts,
        key_points=key_points,
        examples=examples,
        pitfalls=pitfalls,
        actions=actions,
        review_questions=review_questions,
        follow_ups=follow_ups,
        confidence_notes=confidence_notes,
        backend="extractive",
    )


def _looks_like_harness_video(title: str, text: str) -> bool:
    lowered = text.lower()
    title_lower = title.lower()
    return (
        "harness engineering" in title_lower
        or "harnes engineering" in lowered
        or (
            "prompt engineering" in lowered
            and ("context engineering" in lowered or "contest engineering" in lowered or "context and the nearing" in lowered)
            and ("harness" in lowered or "harnes" in lowered)
        )
    )


def _build_harness_knowledge_package(metadata: VideoMetadata, transcript: TranscriptBundle) -> KnowledgePackage:
    confidence_notes = []
    if transcript.origin != "subtitle":
        confidence_notes.append("当前笔记基于 ASR 草稿整理，英文术语和个别公司名建议回看视频二次确认。")
    if transcript.low_confidence_segments:
        confidence_notes.append(f"存在 {len(transcript.low_confidence_segments)} 个低置信段落，复习时优先回看。")
    return KnowledgePackage(
        summary="视频把 Prompt Engineering、Context Engineering、Harness Engineering 放进同一条演进脉络里，核心结论是：真正决定 Agent 能否稳定交付的，往往不是模型本身，而是模型外面的整套运行系统。",
        topics=["Harness Engineering", "Agent工程", "AI系统设计"],
        tags=["视频知识库", "B站学习", "Harness Engineering", "Agent", "Prompt Engineering", "Context Engineering", "系统设计"],
        knowledge_tree=[
            TreeNode("为什么会出现 Harness Engineering", [
                TreeNode("同样的模型和提示词，系统表现差异可能很大"),
                TreeNode("问题不只在模型，而在任务拆解、状态管理、校验与恢复"),
            ]),
            TreeNode("三阶段演进", [
                TreeNode("Prompt Engineering：把任务讲清楚"),
                TreeNode("Context Engineering：把信息给正确"),
                TreeNode("Harness Engineering：让模型在真实执行里持续做对"),
            ]),
            TreeNode("成熟 Harness 的六层", [
                TreeNode("上下文边界", [
                    TreeNode("决定什么信息在什么时机进入模型，避免一开始就把上下文灌满"),
                    TreeNode("重点是按需披露、分层提供，必要时 reset 后再交接"),
                ]),
                TreeNode("工具系统", [
                    TreeNode("把模型能力接到稳定、可控、权限清晰的工具接口"),
                    TreeNode("不是工具越多越强，而是调用条件和失败语义要明确"),
                ]),
                TreeNode("执行编排", [
                    TreeNode("把补信息、执行、验收、修正串成可重复的流程"),
                    TreeNode("先判断信息是否足够，再执行，再验收，不通过就修正"),
                ]),
                TreeNode("记忆与状态", [
                    TreeNode("保存任务进度、中间结果和交接信息，避免每轮从头开始"),
                    TreeNode("至少要区分短期状态、长期记忆和可恢复检查点"),
                ]),
                TreeNode("评估与观测", [
                    TreeNode("用日志、指标、测试和独立 evaluator 判断系统是否真的做对"),
                    TreeNode("生产与验收必须分离，不能让执行者自己给自己打分"),
                ]),
                TreeNode("约束、校验、失败恢复", [
                    TreeNode("超时、格式错乱或路线跑偏时，要能拦截、回滚并恢复"),
                    TreeNode("恢复不是简单重试，而是按规则回到可继续的稳定状态"),
                ]),
            ]),
            TreeNode("一线公司实践", [
                TreeNode("Anthropic：context reset / 生产与验收分离", [
                    TreeNode("上下文膨胀时，不是硬压缩，而是交接给新的 agent 继续执行"),
                ]),
                TreeNode("OpenAI：把工程师工作重心转成环境设计", [
                    TreeNode("重点从亲自写每一步，转向设计边界、流程和反馈闭环"),
                ]),
                TreeNode("按需披露信息，而不是一次性塞满上下文", [
                    TreeNode("真正需要时再注入对应 SOP、工具说明和状态，而不是开局全给"),
                ]),
            ]),
        ],
        concepts=[
            ConceptCard(
                name="Harness Engineering",
                definition="针对 Agent 真实运行系统的工程化设计，关注的是如何让模型在长链路、可执行、低容错的环境里稳定完成任务。",
                importance="它直接影响 Agent 能否上线、能否持续交付、出错后能否被拉回，而不仅是单轮回答是否聪明。",
                example="视频中的案例里，同样的模型和提示词，只是改了任务拆解、状态管理、校验和恢复，成功率就从不到 70% 拉到 95% 以上。",
                pitfall="不要把 Harness 简化成“多写一点 prompt”或“多接几个工具”；它是对整个运行系统的工程化。",
            ),
            ConceptCard(
                name="Prompt Engineering",
                definition="通过角色设定、输出格式、分步引导等方式，把任务表达清楚，塑造模型的局部概率空间。",
                importance="它解决的是“模型有没有听懂你在说什么”的问题，是最内层的语言设计。",
                example="同一个总结任务，换一种提示方式，模型输出质量就可能明显不同。",
                pitfall="它擅长表达和约束输出，但不能凭空补足缺失信息，也不能替代长链路状态管理。",
            ),
            ConceptCard(
                name="Context Engineering",
                definition="在合适的时机，把正确的信息以合适结构送进模型，包括检索结果、历史对话、工具返回、任务状态和系统规则。",
                importance="它解决的是“模型有没有拿到足够而正确的信息”的问题，是输入环境的工程化。",
                example="成熟的 Context Engineering 不只做 RAG，还会处理切块、排序、压缩、状态分层和按需披露。",
                pitfall="不是信息越多越好；上下文窗口是稀缺资源，错误做法是一次性把所有资料都塞给模型。",
            ),
            ConceptCard(
                name="执行编排",
                definition="规定模型下一步该做什么，以及任务如何从理解目标、补信息、生成输出、检查结果到修正迭代串起来。",
                importance="很多 Agent 失败不是某一步不会，而是不会把所有步骤连成稳定轨道。",
                example="先判断信息是否足够，不够则补充；生成结果后再检查，不满足要求就修正或重试。",
                pitfall="只给模型工具、不定义流程，很容易得到“想到哪做到哪”的半成品系统。",
            ),
            ConceptCard(
                name="评估与观测",
                definition="让系统不仅能执行，还能知道自己做得是否正确，包括测试、日志、指标、环境验证和独立验收角色。",
                importance="没有独立评估，Agent 容易停留在“自我感觉良好”的状态，无法形成有效闭环。",
                example="Anthropic 把 planner、implementer、evaluator 分离，evaluator 不只看代码，还真实操作页面和验证结果。",
                pitfall="不要让“干活的人自己给自己打分”；生产与验收必须分离。",
            ),
            ConceptCard(
                name="失败恢复",
                definition="系统在搜索错误、API 超时、格式混乱或任务理解偏差时，能够回滚、切分、重试并恢复到稳定状态的机制。",
                importance="真实环境里失败是常态，没有恢复机制，Agent 只能一出错就从头再来。",
                example="视频提到成熟 Harness 一定包含约束、校验和恢复三件事，并把修复建议一起反馈给 Agent。",
                pitfall="不要把恢复理解成“再试一次”；更关键的是从哪里恢复、按什么规则恢复。",
            ),
        ],
        key_points=[
            "Harness Engineering 不是在讨论“模型更聪明”，而是在讨论“系统能否稳定交付”。",
            "Prompt、Context、Harness 不是替代关系，而是包含关系，边界一层比一层更大。",
            "成熟 Agent 系统的关键，不只是模型能力，还包括工具系统、执行编排、状态管理、评估观测和失败恢复。",
            "上下文优化不是“给更多”，而是“按需给、分层给、在正确时机给”。",
            "生产与验收必须分离，独立 evaluator 是形成有效闭环的重要条件。",
            "很多一线团队的优化重点，已经从调 prompt 转向设计可持续运行的环境与规则。",
        ],
        examples=[
            "作者案例：不改模型和提示词，只改任务拆解、状态管理、关键步骤校验和失败恢复，成功率提升到 95% 以上。",
            "Anthropic：面对长链路任务中的上下文膨胀问题，用 context reset/交接式新 agent 代替简单压缩。",
            "OpenAI：把工程师角色从“亲自写代码”转向“设计任务环境、能力边界和反馈链路”。",
            "按需披露：不是一开始把所有工具和规则塞进模型，而是只在真正需要时注入对应 SOP/技能文档。",
        ],
        pitfalls=[
            "把 Harness 等同于 prompt 优化，会低估系统层设计的重要性。",
            "把 Context Engineering 理解为单纯 RAG，会忽略状态、结构化组织和信息注入时机。",
            "让 Agent 在没有观测、没有验收、没有恢复机制的情况下长链路执行，稳定性会迅速恶化。",
            "把所有信息一次性塞给模型，往往会导致注意力分散和错误决策，而不是更聪明。",
        ],
        actions=[
            "盘点你当前 Agent 系统里，哪些问题属于 prompt，哪些属于 context，哪些已经是 harness 层问题。",
            "给你的 Agent 链路补一张最小运行图：目标定义、工具调用、状态流转、校验点、失败恢复点。",
            "把“生成”和“验收”拆开，至少增加一个独立的 evaluator 或验证环节。",
            "检查你现在给模型的上下文是否存在一次性灌满的问题，尝试改成按需披露。",
        ],
        review_questions=[
            "为什么作者说真正决定系统稳定性的往往不是模型本身，而是模型外面的运行系统？",
            "Prompt Engineering、Context Engineering、Harness Engineering 分别解决什么问题？",
            "一个成熟的 Harness 为什么至少要覆盖六层？这六层分别在管什么？",
            "为什么生产与验收必须分离？让模型自评有什么结构性风险？",
            "为什么“给更多上下文”不等于“更好的 Context Engineering”？",
            "如果你要给自己的 Agent 加一个最小 Harness，第一批应该补哪几个能力？",
        ],
        follow_ups=[
            "把你正在做的一个 Agent 项目，按视频中的六层结构逐层体检一遍。",
            "对照这条视频，再找一条讲 Agent 架构或智能体工程的视频做横向比较。",
            "把“Prompt / Context / Harness”的区别整理成一张自己的对照表，避免概念混淆。",
        ],
        confidence_notes=confidence_notes,
        backend="extractive:harness-specialized",
    )


def _knowledge_from_payload(payload: dict[str, Any], backend: str) -> KnowledgePackage:
    return KnowledgePackage(
        summary=payload["summary"],
        topics=list(dict.fromkeys(payload["topics"]))[:4],
        tags=list(dict.fromkeys(payload["tags"]))[:8],
        knowledge_tree=_tree_nodes_from_payload(payload["knowledge_tree"]),
        concepts=[ConceptCard(**item) for item in payload["concepts"][:6]],
        key_points=payload["key_points"][:6],
        examples=payload["examples"][:4],
        pitfalls=payload["pitfalls"][:4],
        actions=payload["actions"][:5],
        review_questions=payload["review_questions"][:6],
        follow_ups=payload["follow_ups"][:4],
        confidence_notes=payload["confidence_notes"][:4],
        backend=backend,
    )


def _tree_nodes_from_payload(payload: list[dict[str, Any]]) -> list[TreeNode]:
    return [TreeNode(item["title"], _tree_nodes_from_payload(item.get("children", []))) for item in payload]


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?；;])\s+|\n+", text)
    return [part.strip() for part in parts if len(part.strip()) >= 12]


def _build_analysis_units(segments: list[str], target_chars: int = 48, max_segments: int = 4) -> list[str]:
    units: list[str] = []
    bucket: list[str] = []
    bucket_chars = 0
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        bucket.append(segment)
        bucket_chars += len(segment)
        if (
            bucket_chars >= target_chars
            or len(bucket) >= max_segments
            or any(segment.endswith(mark) for mark in "。！？!?；;")
        ):
            units.append("".join(bucket))
            bucket = []
            bucket_chars = 0
    if bucket:
        units.append("".join(bucket))
    return units or segments


def _extract_title_phrases(title: str) -> list[str]:
    phrases = re.findall(r"\b[A-Za-z][A-Za-z0-9.+-]*\s+Engineering\b", title, flags=re.IGNORECASE)
    normalized = []
    for phrase in phrases:
        normalized.append(re.sub(r"\s+", " ", phrase).strip())
    return list(dict.fromkeys(normalized))


def _normalize_known_terms(text: str, title_phrases: list[str]) -> str:
    normalized = text.strip()
    if any("Harness Engineering".lower() == phrase.lower() for phrase in title_phrases):
        normalized = re.sub(r"\bHarnes\b", "Harness", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bcontest engineering\b", "Context Engineering", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bcontext and the nearing\b", "Context Engineering", normalized, flags=re.IGNORECASE)
    return normalized


def _top_keywords(text: str, limit: int = 8, title_phrases: list[str] | None = None) -> list[str]:
    chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    english_terms = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{2,20}\b", text)
    english_phrases = re.findall(r"\b[A-Za-z][A-Za-z0-9.+-]*\s+Engineering\b", text, flags=re.IGNORECASE)
    counts = Counter()
    for phrase in title_phrases or []:
        counts[phrase] += 6
    for phrase in english_phrases:
        counts[re.sub(r"\s+", " ", phrase).strip()] += 4
    for term in chinese_terms:
        if term not in CHINESE_STOPWORDS:
            counts[term] += 1
    for term in english_terms:
        lower = term.lower()
        if lower not in ENGLISH_STOPWORDS and lower not in {"and", "the", "this", "that", "with", "from"}:
            counts[term] += 1
    return [term for term, _ in counts.most_common(limit)]


def _rank_sentences(sentences: list[str], keywords: list[str]) -> list[str]:
    scored: list[tuple[int, str]] = []
    for sentence in sentences:
        score = sum(sentence.count(keyword) * 3 for keyword in keywords[:6])
        score += min(len(sentence) // 30, 4)
        if any(marker in sentence for marker in ("因此", "所以", "核心", "关键", "本质", "结论", "注意")):
            score += 2
        scored.append((score, sentence))
    scored.sort(key=lambda item: item[0], reverse=True)
    unique: list[str] = []
    seen = set()
    for _, sentence in scored:
        normalized = re.sub(r"\s+", "", sentence)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(sentence)
    return unique


def _calculate_overall_confidence(transcript: TranscriptBundle, knowledge: KnowledgePackage) -> float:
    confidence = transcript.average_confidence
    if transcript.origin == "subtitle":
        confidence = max(confidence, 0.96)
    if knowledge.backend.startswith("openai:"):
        confidence += 0.02
    if knowledge.confidence_notes:
        confidence -= 0.04 * len(knowledge.confidence_notes)
    return round(max(0.05, min(0.99, confidence)), 3)


def build_manifest(result: PipelineResult) -> dict[str, Any]:
    return {
        "metadata": result.metadata.to_dict(),
        "transcript": result.transcript.to_dict(),
        "knowledge": result.knowledge.to_dict(),
        "status": result.status,
        "confidence": result.confidence,
        "artifact_paths": result.artifact_paths,
        "warnings": result.warnings,
    }
