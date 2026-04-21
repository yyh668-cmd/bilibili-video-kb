from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TranscriptSegment:
    start: float
    end: float
    text: str
    confidence: float
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TranscriptBundle:
    origin: str
    language: str
    segments: list[TranscriptSegment]
    source_path: str | None = None
    low_confidence_reason: str | None = None

    @property
    def average_confidence(self) -> float:
        if not self.segments:
            return 0.0
        return sum(segment.confidence for segment in self.segments) / len(self.segments)

    @property
    def low_confidence_segments(self) -> list[TranscriptSegment]:
        return [segment for segment in self.segments if segment.confidence < 0.6]

    def plain_text(self) -> str:
        return "\n".join(segment.text.strip() for segment in self.segments if segment.text.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "origin": self.origin,
            "language": self.language,
            "source_path": self.source_path,
            "low_confidence_reason": self.low_confidence_reason,
            "average_confidence": self.average_confidence,
            "segments": [segment.to_dict() for segment in self.segments],
        }


@dataclass(slots=True)
class ConceptCard:
    name: str
    definition: str
    importance: str
    example: str
    pitfall: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TreeNode:
    title: str
    children: list["TreeNode"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass(slots=True)
class KnowledgePackage:
    summary: str
    topics: list[str]
    tags: list[str]
    knowledge_tree: list[TreeNode]
    concepts: list[ConceptCard]
    key_points: list[str]
    examples: list[str]
    pitfalls: list[str]
    actions: list[str]
    review_questions: list[str]
    follow_ups: list[str]
    confidence_notes: list[str]
    backend: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "topics": self.topics,
            "tags": self.tags,
            "knowledge_tree": [node.to_dict() for node in self.knowledge_tree],
            "concepts": [concept.to_dict() for concept in self.concepts],
            "key_points": self.key_points,
            "examples": self.examples,
            "pitfalls": self.pitfalls,
            "actions": self.actions,
            "review_questions": self.review_questions,
            "follow_ups": self.follow_ups,
            "confidence_notes": self.confidence_notes,
            "backend": self.backend,
        }


@dataclass(slots=True)
class VideoMetadata:
    source_platform: str
    source_url: str
    video_id: str
    title: str
    creator: str
    published_at: str | None
    processed_at: str
    part_title: str | None = None
    part_index: int | None = None
    series_title: str | None = None
    cover_url: str | None = None
    raw_info_path: str | None = None

    def published_year(self) -> str:
        if not self.published_at:
            return datetime.now().strftime("%Y")
        return self.published_at[:4]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PipelineResult:
    metadata: VideoMetadata
    transcript: TranscriptBundle
    knowledge: KnowledgePackage
    status: str
    confidence: float
    run_dir: Path
    artifact_paths: dict[str, str]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "transcript": self.transcript.to_dict(),
            "knowledge": self.knowledge.to_dict(),
            "status": self.status,
            "confidence": self.confidence,
            "run_dir": str(self.run_dir),
            "artifact_paths": self.artifact_paths,
            "warnings": self.warnings,
        }

