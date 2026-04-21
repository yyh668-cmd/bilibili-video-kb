from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from .config import RuntimeConfig
from .models import PipelineResult, TreeNode
from .utils import ensure_parent, now_iso, sanitize_filename, timestamp_label, to_obsidian_link, write_text, yaml_frontmatter
from .xmind_export import write_xmind_package


RELATED_START = "<!-- VIDEO_KB:RELATED_START -->"
RELATED_END = "<!-- VIDEO_KB:RELATED_END -->"


@dataclass(slots=True)
class NoteRecord:
    path: Path
    relative_path: Path
    title: str
    creator: str
    published_at: str
    topics: list[str]
    concepts: list[str]
    xmind_path: str | None


def write_obsidian_package(result: PipelineResult, config: RuntimeConfig) -> dict[str, str]:
    _migrate_existing_library(config)

    year_dir = config.knowledge_notes_root / result.metadata.published_year()
    note_stem = sanitize_filename(f"{result.metadata.video_id} {result.metadata.title}")
    main_note_path = year_dir / f"{note_stem}.md"
    xmind_name = sanitize_filename(f"{result.metadata.video_id} {result.metadata.title}", limit=180) + ".xmind"
    xmind_path = config.xmind_root / xmind_name

    for path in (main_note_path, config.index_note, xmind_path):
        ensure_parent(path)

    write_text(main_note_path, build_main_note(result, config, xmind_path))
    write_xmind_package(result, xmind_path)
    _refresh_navigation_and_links(config)

    return {
        "main_note": str(main_note_path),
        "xmind_map": str(xmind_path),
        "index_note": str(config.index_note),
    }


def build_main_note(result: PipelineResult, config: RuntimeConfig, xmind_path: Path) -> str:
    frontmatter = {
        "type": "video_note",
        "source_platform": result.metadata.source_platform,
        "source_url": result.metadata.source_url,
        "video_id": result.metadata.video_id,
        "title": result.metadata.title,
        "creator": result.metadata.creator,
        "published_at": result.metadata.published_at,
        "processed_at": result.metadata.processed_at,
        "topics": result.knowledge.topics,
        "concepts": [concept.name for concept in result.knowledge.concepts],
        "status": result.status,
        "confidence": result.confidence,
        "xmind_path": str(xmind_path),
        "tags": result.knowledge.tags,
    }

    parts: list[str] = [yaml_frontmatter(frontmatter)]
    parts.append(f"# {result.metadata.title}\n")

    if result.metadata.part_title:
        parts.append("> [!info] 分P信息")
        parts.append(f"> 当前分P：P{result.metadata.part_index or '?'} - {result.metadata.part_title}\n")

    if result.transcript.origin != "subtitle" or result.transcript.low_confidence_segments:
        low_segment_lines = [
            f"> - `{timestamp_label(segment.start)}` {segment.text[:80]}"
            for segment in result.transcript.low_confidence_segments[:6]
        ]
        notes = result.knowledge.confidence_notes or ["当前内容来自 ASR 草稿，请优先回看关键段落。"]
        parts.append("> [!warning] 低置信提醒")
        parts.extend(f"> {line}" for line in notes)
        parts.extend(low_segment_lines)
        parts.append("")

    parts.append("## 快速入口\n")
    parts.append(f"- 原视频：{result.metadata.source_url}")
    parts.append(f"- XMind 导图：[打开 XMind 文件]({xmind_path.as_uri()})")
    parts.append(f"- 作者：{result.metadata.creator}")
    parts.append(f"- 处理时间：{result.metadata.processed_at}")
    parts.append(f"- 转写来源：{result.transcript.origin}")
    parts.append(f"- 整理后端：{result.knowledge.backend}\n")

    parts.append("## 一句话总结\n")
    parts.append(f"{result.knowledge.summary}\n")

    parts.append("## 知识主线\n")
    parts.append(_tree_to_markdown(result.knowledge.knowledge_tree))

    parts.append("## 核心概念\n")
    for concept in result.knowledge.concepts:
        parts.append(f"### {concept.name}\n")
        parts.append(f"- 定义：{concept.definition}")
        parts.append(f"- 为什么重要：{concept.importance}")
        parts.append(f"- 例子：{concept.example}")
        parts.append(f"- 易混点：{concept.pitfall}\n")

    parts.append("## 关键论证\n")
    parts.extend(f"- {item}" for item in result.knowledge.key_points)
    parts.append("")

    if result.knowledge.examples:
        parts.append("## 典型案例\n")
        parts.extend(f"- {item}" for item in result.knowledge.examples)
        parts.append("")

    parts.append("## 易混点与风险\n")
    parts.extend(f"- {item}" for item in result.knowledge.pitfalls)
    parts.append("")

    parts.append("## 行动清单\n")
    parts.extend(f"- {item}" for item in result.knowledge.actions)
    parts.append("")

    parts.append("## 复习问题\n")
    parts.extend(f"- {item}" for item in result.knowledge.review_questions)
    parts.append("")

    parts.append("## 延伸学习\n")
    parts.extend(f"- {item}" for item in result.knowledge.follow_ups)
    parts.append("")

    parts.append("## 检索标签\n")
    parts.append(f"- 主题：{', '.join(result.knowledge.topics)}")
    parts.append(f"- 概念：{', '.join(concept.name for concept in result.knowledge.concepts)}\n")

    parts.append("## 关联视频\n")
    parts.append(RELATED_START)
    parts.append("- 暂无明确关联视频")
    parts.append(RELATED_END)
    parts.append("")

    relative_index = config.index_note.relative_to(config.vault_root)
    parts.append("## 索引入口\n")
    parts.append(f"- {to_obsidian_link(relative_index, '返回总索引')}\n")
    return "\n".join(parts).strip() + "\n"


def _tree_to_markdown(nodes: Iterable[TreeNode], level: int = 0) -> str:
    lines: list[str] = []
    prefix = "  " * level + "- "
    for node in nodes:
        lines.append(f"{prefix}{node.title}")
        if node.children:
            lines.append(_tree_to_markdown(node.children, level + 1))
    return "\n".join(lines) + "\n"


def _refresh_navigation_and_links(config: RuntimeConfig) -> None:
    records = _scan_note_records(config)
    related_map = _build_related_map(records)
    for record in records:
        _write_related_block(record, related_map.get(record.path, []))
    _write_index_note(config, records)


def _scan_note_records(config: RuntimeConfig) -> list[NoteRecord]:
    records: list[NoteRecord] = []
    if not config.knowledge_notes_root.exists():
        return records

    for path in sorted(config.knowledge_notes_root.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        frontmatter = _read_frontmatter(raw)
        if frontmatter.get("type") != "video_note":
            continue
        records.append(
            NoteRecord(
                path=path,
                relative_path=path.relative_to(config.vault_root),
                title=str(frontmatter.get("title") or path.stem),
                creator=str(frontmatter.get("creator") or "unknown"),
                published_at=str(frontmatter.get("published_at") or ""),
                topics=[str(item) for item in frontmatter.get("topics") or []],
                concepts=[str(item) for item in frontmatter.get("concepts") or []],
                xmind_path=str(frontmatter.get("xmind_path") or "") or None,
            )
        )
    return records


def _read_frontmatter(text: str) -> dict[str, object]:
    if not text.startswith("---\n"):
        return {}
    try:
        _, frontmatter, _ = text.split("---", 2)
    except ValueError:
        return {}
    payload = yaml.safe_load(frontmatter)
    return payload if isinstance(payload, dict) else {}


def _build_related_map(records: list[NoteRecord]) -> dict[Path, list[tuple[NoteRecord, list[str], list[str]]]]:
    related_map: dict[Path, list[tuple[NoteRecord, list[str], list[str]]]] = {}
    for record in records:
        candidates: list[tuple[int, str, NoteRecord, list[str], list[str]]] = []
        topic_set = {_normalize(item) for item in record.topics}
        concept_set = {_normalize(item) for item in record.concepts}
        for other in records:
            if other.path == record.path:
                continue
            shared_topics = sorted(topic_set & {_normalize(item) for item in other.topics})
            shared_concepts = sorted(concept_set & {_normalize(item) for item in other.concepts})
            if not shared_topics and not shared_concepts:
                continue
            score = len(shared_topics) * 3 + len(shared_concepts) * 2
            if record.creator == other.creator:
                score += 1
            candidates.append(
                (
                    score,
                    other.published_at,
                    other,
                    _recover_original_terms(shared_topics, record.topics, other.topics),
                    _recover_original_terms(shared_concepts, record.concepts, other.concepts),
                )
            )
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        related_map[record.path] = [(other, topics, concepts) for _, _, other, topics, concepts in candidates[:6]]
    return related_map


def _normalize(value: str) -> str:
    return value.strip().lower()


def _recover_original_terms(shared: list[str], left: list[str], right: list[str]) -> list[str]:
    mapping: dict[str, str] = {}
    for source in left + right:
        mapping.setdefault(_normalize(source), source)
    return [mapping[item] for item in shared if item in mapping]


def _write_related_block(record: NoteRecord, related_items: list[tuple[NoteRecord, list[str], list[str]]]) -> None:
    if related_items:
        lines = []
        for other, shared_topics, shared_concepts in related_items:
            reasons: list[str] = []
            if shared_topics:
                reasons.append("共同主题：" + " / ".join(shared_topics))
            if shared_concepts:
                reasons.append("共同概念：" + " / ".join(shared_concepts))
            reason_text = "；".join(reasons)
            lines.append(f"- {to_obsidian_link(other.relative_path, other.title)}")
            if reason_text:
                lines.append(f"  关联点：{reason_text}")
    else:
        lines = ["- 暂无明确关联视频"]

    block = RELATED_START + "\n" + "\n".join(lines) + "\n" + RELATED_END
    text = record.path.read_text(encoding="utf-8")
    if RELATED_START in text and RELATED_END in text:
        before, rest = text.split(RELATED_START, 1)
        _, after = rest.split(RELATED_END, 1)
        updated = before.rstrip() + "\n" + block + after
    else:
        updated = text.rstrip() + "\n\n## 关联视频\n" + block + "\n"
    write_text(record.path, updated.rstrip() + "\n")


def _write_index_note(config: RuntimeConfig, records: list[NoteRecord]) -> None:
    sorted_records = sorted(records, key=lambda item: (item.published_at, item.title), reverse=True)
    topic_groups: dict[str, list[NoteRecord]] = {}
    for record in sorted_records:
        for topic in record.topics:
            topic_groups.setdefault(topic, []).append(record)

    parts = ["# 视频知识库总索引", ""]
    parts.append("## 最近更新\n")
    if sorted_records:
        for record in sorted_records[:30]:
            parts.append(_index_line(record))
    else:
        parts.append("- 暂无视频笔记")
    parts.append("")

    parts.append("## 按主题导航\n")
    if topic_groups:
        for topic in sorted(topic_groups):
            parts.append(f"### {topic}\n")
            for record in topic_groups[topic]:
                parts.append(_index_line(record))
            parts.append("")
    else:
        parts.append("- 暂无主题")
        parts.append("")

    parts.append("## 全部视频\n")
    if sorted_records:
        for record in sorted_records:
            parts.append(_index_line(record))
    else:
        parts.append("- 暂无视频笔记")
    parts.append("")
    parts.append(f"_last_updated: {now_iso()}_")
    write_text(config.index_note, "\n".join(parts).strip() + "\n")


def _index_line(record: NoteRecord) -> str:
    topics = " / ".join(record.topics[:3]) if record.topics else "未分类"
    suffix = []
    if record.published_at:
        suffix.append(record.published_at)
    if record.creator:
        suffix.append(record.creator)
    suffix.append(f"主题：{topics}")
    if record.xmind_path:
        suffix.append(f"[XMind]({Path(record.xmind_path).as_uri()})")
    return f"- {to_obsidian_link(record.relative_path, record.title)} | " + " | ".join(suffix)


def _migrate_existing_library(config: RuntimeConfig) -> None:
    legacy_notes_root = config.kb_root / "01 视频笔记"
    if legacy_notes_root.exists():
        for legacy_note in legacy_notes_root.rglob("*.md"):
            if legacy_note.name.endswith(" - 导图.md"):
                continue
            relative = legacy_note.relative_to(legacy_notes_root)
            target = config.knowledge_notes_root / relative
            if not target.exists():
                ensure_parent(target)
                shutil.move(str(legacy_note), str(target))
        shutil.rmtree(legacy_notes_root, ignore_errors=True)

    for obsolete in (
        config.kb_root / "00 总览.md",
        config.kb_root / "02 主题索引",
        config.kb_root / "03 概念卡片",
        config.kb_root / "04 转写索引",
    ):
        if obsolete.is_dir():
            shutil.rmtree(obsolete, ignore_errors=True)
        elif obsolete.exists():
            obsolete.unlink()
