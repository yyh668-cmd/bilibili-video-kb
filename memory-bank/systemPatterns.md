# System Patterns

## Architecture

- PowerShell entrypoints:
  - `scripts/setup_video_kb.ps1`
  - `scripts/run_video_kb.ps1`
- Python package:
  - `src/video_kb/cli.py` for CLI entrypoints
  - `src/video_kb/pipeline.py` for ingest, subtitle handling, ASR, and knowledge extraction
  - `src/video_kb/obsidian.py` for note export and index updates
- Cache/output split:
  - cache artifacts under `.cache/video_kb/`
  - readable notes inside the Obsidian vault

## Processing Pattern

1. Accept a Bilibili URL or local media path.
2. If URL:
   - fetch metadata with `yt-dlp`
   - try subtitles first
   - fall back to audio download plus ASR
3. Build a transcript bundle with confidence signals.
4. Generate knowledge notes:
   - OpenAI if configured
   - extractive fallback otherwise
5. Export the note package to Obsidian.
6. Write a cache-side manifest for reruns and debugging.

## Obsidian Export Pattern

- Main note, Markdown mind-map note, XMind map file, and transcript note are generated per video.
- Topic pages and concept cards use managed blocks so future automation can refresh machine-owned sections without requiring a full-file rewrite policy.
- The root overview note stays lightweight and points to recent activity.

## Workflow Pattern

- Keep repo-tracked automation logic in the repository.
- Keep large downloads and intermediate artifacts out of the vault.
- Update memory-bank files whenever the repo purpose or default workflow changes.
- Prefer small, testable changes over opaque one-off scripts.

## Truth Hierarchy

1. Current repository files
2. Verified commands and test runs
3. Memory-bank documents
4. Old chat history
