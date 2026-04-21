# Video KB Automation Workspace

This repository hosts a link-first Bilibili knowledge-video pipeline.

## Primary Workflow

1. Initialize the local environment:

   ```powershell
   .\scripts\setup_video_kb.ps1
   ```

2. Process a Bilibili URL or local media file:

   ```powershell
   .\scripts\run_video_kb.ps1 "https://www.bilibili.com/video/BV1xxxxxx/"
   ```

   Or invoke the repo skill wrapper:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\.agents\skills\bilibili-video-kb\scripts\run-video-kb.ps1 "https://www.bilibili.com/video/BV1xxxxxx/"
   ```

3. Outputs are written to:

- Obsidian vault: `D:\Document\Win_Obsidian知识库\YYH个人知识库\08 视频知识库`
- Desktop XMind folder: `C:\Users\yy198\Desktop\B站视频XMind`

## Obsidian Structure

- `08 视频知识库/01 知识笔记/{年份}/{BV号 标题}.md`
- `08 视频知识库/02 索引导航/总索引.md`

## Outputs Per Run

- one complete knowledge note in Obsidian
- one XMind file in the desktop XMind folder
- automatic related-note links between overlapping videos
- one simplified Obsidian index page
- one cache-side manifest under `.cache/video_kb/`

## Codex Skill

This workspace now includes the reusable skill:

- `.agents/skills/bilibili-video-kb`

Use it when a user sends a Bilibili link and wants the repo workflow to generate the Obsidian note, XMind map, and updated index automatically.

## XMind Compatibility

The exporter writes the legacy XML-based `.xmind` content and then repairs the package by adding the missing `meta.xml` and `META-INF/manifest.xml` files required by the current XMind desktop client.

## Legacy Demo

The small Node demo remains in the repository as legacy material:

```powershell
node server.mjs
```

Then open `http://127.0.0.1:4173`.

## Project Memory

- `AGENTS.md`
- `memory-bank/README.md`
- `memory-bank/activeContext.md`
- `memory-bank/tasks.md`
- `memory-bank/progress.md`
