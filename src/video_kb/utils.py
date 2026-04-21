from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1F]'
CHINESE_STOPWORDS = {
    "我们",
    "你们",
    "他们",
    "这个",
    "那个",
    "因为",
    "所以",
    "然后",
    "如果",
    "就是",
    "一个",
    "一些",
    "已经",
    "进行",
    "视频",
    "知识",
    "内容",
    "问题",
    "时候",
    "可以",
    "需要",
    "这里",
    "还是",
    "以及",
    "这样",
    "什么",
    "没有",
    "不是",
    "比较",
}
ENGLISH_STOPWORDS = {
    "about",
    "after",
    "also",
    "because",
    "being",
    "could",
    "from",
    "have",
    "into",
    "just",
    "like",
    "more",
    "much",
    "only",
    "that",
    "there",
    "these",
    "those",
    "very",
    "what",
    "when",
    "with",
    "would",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sanitize_filename(value: str, limit: int = 120) -> str:
    cleaned = re.sub(INVALID_FILENAME_CHARS, " ", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.rstrip(".")
    if not cleaned:
        cleaned = "untitled"
    return cleaned[:limit]


def slugify(value: str) -> str:
    text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", value).strip("-").lower()
    return text or "item"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def yaml_frontmatter(data: dict[str, Any]) -> str:
    return "---\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False).strip() + "\n---\n"


def chunked_text(lines: Iterable[str], separator: str = "\n") -> str:
    return separator.join(line for line in lines if line)


def to_obsidian_link(relative_path: Path, alias: str | None = None) -> str:
    target = relative_path.as_posix()
    stem = target[:-3] if target.endswith(".md") else target
    return f"[[{stem}|{alias}]]" if alias else f"[[{stem}]]"


def timestamp_label(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

