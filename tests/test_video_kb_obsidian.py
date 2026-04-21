from __future__ import annotations

import zipfile
from pathlib import Path

from video_kb.config import RuntimeConfig
from video_kb.models import ConceptCard, KnowledgePackage, PipelineResult, TranscriptBundle, TranscriptSegment, TreeNode, VideoMetadata
from video_kb.obsidian import build_main_note, write_obsidian_package
from video_kb.xmind_export import write_xmind_package


def sample_result(tmp_path: Path, *, video_id: str = "BV1test-P1", title: str = "样例知识视频", topics: list[str] | None = None) -> PipelineResult:
    metadata = VideoMetadata(
        source_platform="bilibili",
        source_url=f"https://www.bilibili.com/video/{video_id}/",
        video_id=video_id,
        title=title,
        creator="样例UP",
        published_at="2026-04-20",
        processed_at="2026-04-20T12:00:00+08:00",
        part_title="第一节",
        part_index=1,
    )
    transcript = TranscriptBundle(
        origin="asr",
        language="zh",
        low_confidence_reason="字幕缺失，已回退到本地 ASR 草稿。",
        segments=[
            TranscriptSegment(0.0, 4.2, "第一段讲核心定义。", 0.95, "asr"),
            TranscriptSegment(4.2, 7.0, "第二段讲常见误区。", 0.45, "asr"),
        ],
    )
    knowledge = KnowledgePackage(
        summary="视频解释了核心定义和常见误区。",
        topics=topics or ["控制理论", "概念辨析"],
        tags=["视频知识库", "控制理论", "概念辨析"],
        knowledge_tree=[TreeNode("主线", [TreeNode("核心定义"), TreeNode("误区")])],
        concepts=[
            ConceptCard(
                name="核心定义",
                definition="用于建立理解基线。",
                importance="如果不先掌握定义，就无法判断后续结论。",
                example="视频前半段给了直接例子。",
                pitfall="只背结论，不看适用条件。",
            )
        ],
        key_points=["先理解定义，再看误区。"],
        examples=["用一个反例说明为什么会误判。"],
        pitfalls=["不要把定义和结论混在一起。"],
        actions=["先复述定义。"],
        review_questions=["你能不用原文解释定义吗？"],
        follow_ups=["再找一条相关视频比较。"],
        confidence_notes=["当前笔记基于 ASR 草稿生成，关键术语需要人工抽查。"],
        backend="extractive",
    )
    return PipelineResult(
        metadata=metadata,
        transcript=transcript,
        knowledge=knowledge,
        status="draft",
        confidence=0.61,
        run_dir=tmp_path / "run",
        artifact_paths={},
        warnings=[],
    )


def test_build_main_note_contains_required_sections(tmp_path: Path) -> None:
    config = RuntimeConfig(
        vault_root=tmp_path / "vault",
        kb_root=tmp_path / "vault" / "08 视频知识库",
        cache_root=tmp_path / ".cache",
        xmind_root=tmp_path / "desktop" / "B站视频XMind",
    )
    result = sample_result(tmp_path)
    note = build_main_note(result, config, config.xmind_root / "样例知识视频.xmind")
    assert "## 一句话总结" in note
    assert "## 知识主线" in note
    assert "## 复习问题" in note
    assert "低置信提醒" in note
    assert "## 关联视频" in note
    assert "source_platform: bilibili" in note


def test_write_obsidian_package_creates_note_index_and_xmind(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    config = RuntimeConfig(
        vault_root=vault_root,
        kb_root=vault_root / "08 视频知识库",
        cache_root=tmp_path / ".cache",
        xmind_root=tmp_path / "desktop" / "B站视频XMind",
    )
    result = sample_result(tmp_path)
    artifact_paths = write_obsidian_package(result, config)
    assert Path(artifact_paths["main_note"]).exists()
    assert Path(artifact_paths["xmind_map"]).exists()
    assert Path(artifact_paths["index_note"]).exists()
    assert "topic::" not in "".join(artifact_paths.keys())
    assert "concept::" not in "".join(artifact_paths.keys())
    with zipfile.ZipFile(artifact_paths["xmind_map"], "r") as xmind_file:
        names = set(xmind_file.namelist())
        content = xmind_file.read("content.xml").decode("utf-8")
        styles = xmind_file.read("styles.xml").decode("utf-8")
    assert "META-INF/manifest.xml" in names
    assert "meta.xml" in names
    assert 'style-id="topic-root"' in content
    assert 'style-id="branch-knowledge"' in content
    assert 'id="branch-knowledge"' in styles


def test_related_video_links_are_written_back_to_existing_notes(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    config = RuntimeConfig(
        vault_root=vault_root,
        kb_root=vault_root / "08 视频知识库",
        cache_root=tmp_path / ".cache",
        xmind_root=tmp_path / "desktop" / "B站视频XMind",
    )
    first = sample_result(tmp_path / "a", video_id="BV1first", title="第一条视频", topics=["Agent工程", "系统设计"])
    second = sample_result(tmp_path / "b", video_id="BV1second", title="第二条视频", topics=["Agent工程", "工作流"])

    first_paths = write_obsidian_package(first, config)
    second_paths = write_obsidian_package(second, config)

    first_note = Path(first_paths["main_note"]).read_text(encoding="utf-8")
    second_note = Path(second_paths["main_note"]).read_text(encoding="utf-8")
    assert "第二条视频" in first_note
    assert "第一条视频" in second_note


def test_xmind_export_adds_detail_nodes_for_knowledge_tree(tmp_path: Path) -> None:
    result = sample_result(tmp_path, title="Harness 样例")
    result.knowledge = KnowledgePackage(
        summary="样例总结。",
        topics=["Harness Engineering"],
        tags=["视频知识库", "Harness Engineering"],
        knowledge_tree=[TreeNode("成熟 Harness 的六层", [TreeNode("执行编排")])],
        concepts=[],
        key_points=["关键点样例"],
        examples=[],
        pitfalls=[],
        actions=[],
        review_questions=[],
        follow_ups=[],
        confidence_notes=[],
        backend="extractive",
    )
    xmind_path = tmp_path / "detail-map.xmind"
    write_xmind_package(result, xmind_path)

    with zipfile.ZipFile(xmind_path, "r") as xmind_file:
        content = xmind_file.read("content.xml").decode("utf-8")

    assert "作用：把补信息、执行、验收、修正串成稳定流程" in content
    assert "抓手：先判断信息是否足够，再执行、验收和修正" in content
