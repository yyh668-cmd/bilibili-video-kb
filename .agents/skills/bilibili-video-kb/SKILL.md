---
name: bilibili-video-kb
description: "Convert a Bilibili knowledge-video link or local media file into the repository's study artifacts: a full Obsidian knowledge note, a desktop XMind map, and an updated navigation index. Use when the user sends a Bilibili video link, asks to extract knowledge from a video, wants a study-ready note in Obsidian, wants an XMind mind map, or wants to reprocess an existing video after workflow improvements."
---

# Bilibili Video KB

Run the repository pipeline instead of manually rewriting notes. This skill is the entry point for the local video knowledge workflow.

## Quick Start

From the repository root, run:

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/bilibili-video-kb/scripts/run-video-kb.ps1 "<bilibili-url-or-local-media-path>"
```

The helper script reuses the repo's canonical workflow:

- `scripts/setup_video_kb.ps1`
- `scripts/run_video_kb.ps1`

## Workflow

1. Treat the user input as one video unless batch processing is explicitly requested.
2. Invoke the helper script with the URL or local media path.
3. Read the command output and report these artifacts back to the user:
- main note
- index note
- XMind map
- run manifest
4. Surface warnings explicitly, especially:
- subtitle missing
- ASR fallback
- low-confidence transcript segments
- OpenAI unavailable or extractive fallback
5. If the user asks for a refreshed result after extractor or exporter changes, rerun the same link. The updated note and XMind file should replace the earlier version at the same paths.

## Defaults

- Vault root: `D:\Document\Win_Obsidian知识库\YYH个人知识库`
- XMind root: `C:\Users\yy198\Desktop\B站视频XMind`
- Obsidian structure:
  - `08 视频知识库/01 知识笔记`
  - `08 视频知识库/02 索引导航`
- Rich visual detail belongs in XMind. Do not recreate deprecated Markdown mind maps, topic pages, transcript pages, or concept-card folders.

## Failure Handling

- If `.venv-video-kb` is missing, let the helper script run setup first.
- If `OPENAI_API_KEY` is missing, continue in extractive mode and mention the downgrade.
- If the ingest command fails, inspect the emitted error before suggesting manual workarounds.
- Use the `run_manifest.json` path from command output when you need the precise warning or artifact payload.

## Output Contract

After a successful run, respond concisely with the concrete local paths to:

- the generated Obsidian note
- the generated XMind file
- the updated index note
- the run manifest
