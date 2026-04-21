# Project Brief

## Project

Video KB Automation Workspace

## Purpose

Build a repeatable pipeline that turns Bilibili knowledge videos into:

- one complete Obsidian knowledge note
- one simple Obsidian navigation index
- one desktop XMind file

## Current Goal

Stabilize the simplified v1 workflow:

- subtitle-first
- ASR fallback
- OpenAI-first extraction with extractive fallback
- minimal Obsidian structure
- desktop XMind export
- automatic related-video links

## Success Criteria

- A single command can process a Bilibili URL or a local media file.
- Obsidian only contains `01 知识笔记` and `02 索引导航`.
- Every successful run creates one `.xmind` file in the desktop XMind folder.
- Related videos can jump to each other from inside Obsidian notes.
- Cache artifacts stay outside the vault in `.cache/video_kb/`.

## Non-Goals

- speaker diarization as a hard dependency
- vector databases or external retrieval systems
- a complex multi-layer Obsidian structure
