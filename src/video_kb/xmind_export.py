from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
import xml.sax.saxutils as xml_utils
import zipfile
from dataclasses import dataclass
from pathlib import Path
import re

import xmind

from .models import ConceptCard, PipelineResult, TreeNode


CONTENT_NS = "urn:xmind:xmap:xmlns:content:2.0"
STYLE_NS = "urn:xmind:xmap:xmlns:style:2.0"
FO_NS = "http://www.w3.org/1999/XSL/Format"
SVG_NS = "http://www.w3.org/2000/svg"
XHTML_NS = "http://www.w3.org/1999/xhtml"
XLINK_NS = "http://www.w3.org/1999/xlink"

TOPIC_ROOT_STYLE_ID = "topic-root"
GENERIC_BRANCH_KEY = "generic"

TOP_LEVEL_BRANCH_KEYS = {
    "视频定位": "orientation",
    "分P信息": "part",
    "知识主干": "knowledge",
    "核心概念": "concepts",
    "关键论证": "arguments",
    "典型案例": "examples",
    "易混点与风险": "risks",
    "行动清单": "actions",
    "复习问题": "review",
    "延伸学习": "followups",
    "置信提醒": "confidence",
}

GENERIC_NODE_DETAILS = {
    "上下文边界": [
        "作用：控制信息进入模型的时机，避免一次性灌满上下文",
        "抓手：按需披露、分层提供，必要时 reset 后再交接",
    ],
    "工具系统": [
        "作用：把模型能力接到稳定、可控、权限清晰的工具接口",
        "抓手：重点不是工具多，而是调用条件、返回格式、失败语义明确",
    ],
    "执行编排": [
        "作用：把补信息、执行、验收、修正串成稳定流程",
        "抓手：先判断信息是否足够，再执行、验收和修正",
    ],
    "记忆与状态": [
        "作用：保存任务进度、中间结果和交接信息，避免每轮从头开始",
        "抓手：区分短期状态、长期记忆和可恢复检查点",
    ],
    "评估与观测": [
        "作用：用日志、指标、测试和独立验收判断系统是否真的做对",
        "抓手：生产与验收分离，不能让执行者自己给自己打分",
    ],
    "约束、校验、失败恢复": [
        "作用：在超时、格式错乱或路线跑偏时拦截、回滚并恢复",
        "抓手：恢复不只是重试，而是按规则回到可继续的稳定状态",
    ],
}


for prefix, uri in (
    ("", CONTENT_NS),
    ("fo", FO_NS),
    ("svg", SVG_NS),
    ("xhtml", XHTML_NS),
    ("xlink", XLINK_NS),
):
    ET.register_namespace(prefix, uri)


@dataclass(frozen=True)
class TopicPalette:
    branch_fill: str
    branch_text: str
    branch_stroke: str
    sub_fill: str
    sub_text: str
    sub_stroke: str
    detail_fill: str
    detail_text: str
    detail_stroke: str


PALETTES: dict[str, TopicPalette] = {
    "orientation": TopicPalette("#2563EB", "#F8FAFC", "#1D4ED8", "#DBEAFE", "#1E3A8A", "#93C5FD", "#EFF6FF", "#1D4ED8", "#BFDBFE"),
    "part": TopicPalette("#4F46E5", "#F8FAFC", "#4338CA", "#E0E7FF", "#3730A3", "#A5B4FC", "#EEF2FF", "#4338CA", "#C7D2FE"),
    "knowledge": TopicPalette("#EA580C", "#FFF7ED", "#C2410C", "#FFEDD5", "#9A3412", "#FDBA74", "#FFF7ED", "#C2410C", "#FED7AA"),
    "concepts": TopicPalette("#0F766E", "#F0FDFA", "#115E59", "#CCFBF1", "#134E4A", "#5EEAD4", "#F0FDFA", "#0F766E", "#99F6E4"),
    "arguments": TopicPalette("#7C3AED", "#F5F3FF", "#6D28D9", "#EDE9FE", "#5B21B6", "#C4B5FD", "#F5F3FF", "#6D28D9", "#DDD6FE"),
    "examples": TopicPalette("#059669", "#ECFDF5", "#047857", "#D1FAE5", "#065F46", "#6EE7B7", "#F0FDF4", "#047857", "#A7F3D0"),
    "risks": TopicPalette("#DC2626", "#FEF2F2", "#B91C1C", "#FEE2E2", "#991B1B", "#FCA5A5", "#FEF2F2", "#B91C1C", "#FECACA"),
    "actions": TopicPalette("#15803D", "#F0FDF4", "#166534", "#DCFCE7", "#166534", "#86EFAC", "#F7FEE7", "#166534", "#BBF7D0"),
    "review": TopicPalette("#0891B2", "#ECFEFF", "#0E7490", "#CFFAFE", "#155E75", "#67E8F9", "#F0FDFF", "#0E7490", "#A5F3FC"),
    "followups": TopicPalette("#7C3AED", "#F5F3FF", "#6D28D9", "#EDE9FE", "#5B21B6", "#C4B5FD", "#FAF5FF", "#6D28D9", "#E9D5FF"),
    "confidence": TopicPalette("#92400E", "#FFFBEB", "#78350F", "#FEF3C7", "#78350F", "#FCD34D", "#FFFBEB", "#92400E", "#FDE68A"),
    GENERIC_BRANCH_KEY: TopicPalette("#334155", "#F8FAFC", "#1E293B", "#E2E8F0", "#334155", "#CBD5E1", "#F8FAFC", "#475569", "#E2E8F0"),
}


def write_xmind_package(result: PipelineResult, xmind_path: Path) -> str:
    result.run_dir.mkdir(parents=True, exist_ok=True)
    xmind_path.parent.mkdir(parents=True, exist_ok=True)

    detail_lookup = _build_detail_lookup(result)

    temp_path = result.run_dir / f"{result.metadata.video_id}-xmind-export.xmind"
    workbook = xmind.load(str(temp_path))
    sheet = workbook.getPrimarySheet()
    sheet.setTitle("视频知识导图")

    root = sheet.getRootTopic()
    root.setTitle(result.metadata.title)
    root.setURLHyperlink(result.metadata.source_url)
    root.setStructureClass("org.xmind.ui.logic.right")
    root.setPlainNotes(
        "\n".join(
            [
                f"作者: {result.metadata.creator}",
                f"发布时间: {result.metadata.published_at or 'unknown'}",
                f"处理时间: {result.metadata.processed_at}",
                f"转写来源: {result.transcript.origin}",
                f"知识抽取后端: {result.knowledge.backend}",
            ]
        )
    )

    _append_branch(
        root,
        "视频定位",
        [
            "主题: " + " / ".join(result.knowledge.topics),
            "一句话总结: " + result.knowledge.summary,
            "作者: " + result.metadata.creator,
            "状态: " + result.status,
            f"置信度: {result.confidence:.2f}",
        ],
    )
    if result.metadata.part_title:
        _append_branch(
            root,
            "分P信息",
            [
                f"当前分P: P{result.metadata.part_index or '?'}",
                f"标题: {result.metadata.part_title}",
            ],
        )

    _append_tree_branch(root, "知识主干", result.knowledge.knowledge_tree, detail_lookup)
    _append_concepts_branch(root, result.knowledge.concepts)
    _append_branch(root, "关键论证", result.knowledge.key_points)
    _append_branch(root, "典型案例", result.knowledge.examples)
    _append_branch(root, "易混点与风险", result.knowledge.pitfalls)
    _append_branch(root, "行动清单", result.knowledge.actions)
    _append_branch(root, "复习问题", result.knowledge.review_questions)
    _append_branch(root, "延伸学习", result.knowledge.follow_ups)
    if result.knowledge.confidence_notes:
        _append_branch(root, "置信提醒", result.knowledge.confidence_notes)

    xmind.save(workbook, path=str(temp_path))
    shutil.copyfile(temp_path, xmind_path)
    _finalize_xmind_package(xmind_path, processed_at=result.metadata.processed_at)
    return str(xmind_path)


def _append_branch(parent, title: str, items: list[str]) -> None:
    if not items:
        return
    topic = parent.addSubTopic()
    topic.setTitle(title)
    for item in items:
        text = item.strip()
        if not text:
            continue
        child = topic.addSubTopic()
        child.setTitle(text)


def _append_tree_branch(parent, title: str, nodes: list[TreeNode], detail_lookup: dict[str, list[str]]) -> None:
    if not nodes:
        return
    topic = parent.addSubTopic()
    topic.setTitle(title)
    for node in nodes:
        _append_tree_node(topic, node, detail_lookup)


def _append_tree_node(parent, node: TreeNode, detail_lookup: dict[str, list[str]]) -> None:
    topic = parent.addSubTopic()
    topic.setTitle(node.title)
    if node.children:
        for child in node.children:
            _append_tree_node(topic, child, detail_lookup)
        return

    for detail in detail_lookup.get(_normalize_topic_key(node.title), []):
        child = topic.addSubTopic()
        child.setTitle(detail)


def _append_concepts_branch(parent, concepts: list[ConceptCard]) -> None:
    if not concepts:
        return
    branch = parent.addSubTopic()
    branch.setTitle("核心概念")
    for concept in concepts:
        topic = branch.addSubTopic()
        topic.setTitle(concept.name)
        for line in (
            "定义: " + concept.definition,
            "重要性: " + concept.importance,
            "例子: " + concept.example,
            "易混点: " + concept.pitfall,
        ):
            child = topic.addSubTopic()
            child.setTitle(line)


def _build_detail_lookup(result: PipelineResult) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for title, lines in GENERIC_NODE_DETAILS.items():
        _merge_detail_lines(lookup, title, lines)

    for concept in result.knowledge.concepts:
        _merge_detail_lines(
            lookup,
            concept.name,
            [
                "作用：" + _compact_text(concept.definition),
                "重点：" + _compact_text(concept.importance),
            ],
        )

    return lookup


def _merge_detail_lines(lookup: dict[str, list[str]], title: str, lines: list[str]) -> None:
    key = _normalize_topic_key(title)
    bucket = lookup.setdefault(key, [])
    seen = {_normalize_topic_key(item) for item in bucket}
    for line in lines:
        text = line.strip()
        if not text:
            continue
        normalized = _normalize_topic_key(text)
        if normalized in seen:
            continue
        bucket.append(text)
        seen.add(normalized)
    del bucket[2:]


def _compact_text(text: str, limit: int = 30) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip("，、；：: ") + "…"


def _normalize_topic_key(text: str) -> str:
    return re.sub(r"[\s:：、，,。；;（）()【】\\[\\]<>《》/\\\\-]+", "", text).lower()


def _finalize_xmind_package(xmind_path: Path, *, processed_at: str) -> None:
    with zipfile.ZipFile(xmind_path, "r") as source:
        payloads = {name: source.read(name) for name in source.namelist()}

    payloads["content.xml"] = _apply_visual_styles(payloads["content.xml"])
    payloads["styles.xml"] = _build_styles_xml().encode("utf-8")
    payloads["meta.xml"] = _build_meta_xml(processed_at).encode("utf-8")
    manifest_names = sorted(set(payloads) | {"META-INF/manifest.xml"})
    payloads["META-INF/manifest.xml"] = _build_manifest_xml(manifest_names).encode("utf-8")

    temp_path = xmind_path.with_suffix(".fixed.xmind")
    with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name in sorted(payloads):
            target.writestr(name, payloads[name])
    temp_path.replace(xmind_path)


def _apply_visual_styles(content_xml: bytes) -> bytes:
    root = ET.fromstring(content_xml)
    root_topic = root.find(f"./{{{CONTENT_NS}}}sheet/{{{CONTENT_NS}}}topic")
    if root_topic is None:
        return content_xml

    root_topic.set("style-id", TOPIC_ROOT_STYLE_ID)
    for branch in _attached_topics(root_topic):
        branch_key = TOP_LEVEL_BRANCH_KEYS.get(_topic_title(branch), GENERIC_BRANCH_KEY)
        branch.set("style-id", f"branch-{branch_key}")
        _apply_descendant_styles(branch, branch_key, absolute_depth=2)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _apply_descendant_styles(topic: ET.Element, branch_key: str, *, absolute_depth: int) -> None:
    for child in _attached_topics(topic):
        has_children = bool(_attached_topics(child))
        if absolute_depth == 2 or has_children:
            child.set("style-id", f"sub-{branch_key}")
        else:
            child.set("style-id", f"detail-{branch_key}")
        _apply_descendant_styles(child, branch_key, absolute_depth=absolute_depth + 1)


def _attached_topics(topic: ET.Element) -> list[ET.Element]:
    children = topic.find(f"./{{{CONTENT_NS}}}children")
    if children is None:
        return []
    attached = children.find(f"./{{{CONTENT_NS}}}topics[@type='attached']")
    if attached is None:
        return []
    return list(attached.findall(f"./{{{CONTENT_NS}}}topic"))


def _topic_title(topic: ET.Element) -> str:
    title = topic.find(f"./{{{CONTENT_NS}}}title")
    return (title.text or "").strip() if title is not None else ""


def _build_styles_xml() -> str:
    ET.register_namespace("", STYLE_NS)
    ET.register_namespace("fo", FO_NS)
    ET.register_namespace("svg", SVG_NS)

    root = ET.Element(f"{{{STYLE_NS}}}xmap-styles", {"version": "2.0"})
    styles = ET.SubElement(root, f"{{{STYLE_NS}}}styles")

    _append_style(
        styles,
        TOPIC_ROOT_STYLE_ID,
        fill="#0F172A",
        text="#F8FAFC",
        stroke="#1E3A8A",
        font_size="18pt",
        font_weight="bold",
    )

    for key, palette in PALETTES.items():
        _append_style(
            styles,
            f"branch-{key}",
            fill=palette.branch_fill,
            text=palette.branch_text,
            stroke=palette.branch_stroke,
            font_size="15pt",
            font_weight="bold",
        )
        _append_style(
            styles,
            f"sub-{key}",
            fill=palette.sub_fill,
            text=palette.sub_text,
            stroke=palette.sub_stroke,
            font_size="12pt",
            font_weight="bold",
        )
        _append_style(
            styles,
            f"detail-{key}",
            fill=palette.detail_fill,
            text=palette.detail_text,
            stroke=palette.detail_stroke,
            font_size="11pt",
            font_weight="normal",
        )

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def _append_style(
    styles: ET.Element,
    style_id: str,
    *,
    fill: str,
    text: str,
    stroke: str,
    font_size: str,
    font_weight: str,
) -> None:
    style = ET.SubElement(styles, f"{{{STYLE_NS}}}style", {"id": style_id, "type": "topic"})
    properties = ET.SubElement(style, f"{{{STYLE_NS}}}topic-properties")
    properties.set(f"{{{SVG_NS}}}fill", fill)
    properties.set(f"{{{SVG_NS}}}stroke", stroke)
    properties.set(f"{{{SVG_NS}}}stroke-width", "1")
    properties.set(f"{{{FO_NS}}}color", text)
    properties.set(f"{{{FO_NS}}}font-size", font_size)
    properties.set(f"{{{FO_NS}}}font-weight", font_weight)


def _build_meta_xml(processed_at: str) -> str:
    escaped_time = xml_utils.escape(processed_at)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">\n'
        "  <Creator>video-kb-automation</Creator>\n"
        f"  <CreateTime>{escaped_time}</CreateTime>\n"
        "  <Modifier>video-kb-automation</Modifier>\n"
        f"  <ModifyTime>{escaped_time}</ModifyTime>\n"
        "</meta>\n"
    )


def _build_manifest_xml(file_names: list[str]) -> str:
    directory_names = {"META-INF/"}
    for file_name in file_names:
        parts = file_name.split("/")[:-1]
        prefix = ""
        for part in parts:
            prefix = f"{prefix}{part}/"
            directory_names.add(prefix)

    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0" password-hint="">',
    ]
    for directory_name in sorted(directory_names):
        lines.append(f'  <file-entry full-path="{xml_utils.escape(directory_name)}" media-type=""/>')
    for file_name in file_names:
        lines.append(
            '  <file-entry full-path="{path}" media-type="{media_type}"/>'.format(
                path=xml_utils.escape(file_name),
                media_type=_media_type(file_name),
            )
        )
    lines.append("</manifest>")
    return "\n".join(lines) + "\n"


def _media_type(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    return {
        ".xml": "text/xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".json": "application/json",
    }.get(suffix, "")
