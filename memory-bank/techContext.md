# Tech Context

## Stack

- Python 3.10+
- PowerShell
- `yt-dlp`
- `faster-whisper`
- `PyYAML`
- `xmind`
- optional `openai`
- legacy Node.js static demo

## Key Commands

Environment setup:

```powershell
.\scripts\setup_video_kb.ps1
```

Run the pipeline:

```powershell
.\scripts\run_video_kb.ps1 "https://www.bilibili.com/video/BV1xxxxxx/"
```

Run the repo skill wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File .\.agents\skills\bilibili-video-kb\scripts\run-video-kb.ps1 "https://www.bilibili.com/video/BV1xxxxxx/"
```

Direct Python CLI:

```powershell
.venv-video-kb\Scripts\python.exe -m video_kb.cli ingest "<url-or-path>"
```

Dependency check:

```powershell
.venv-video-kb\Scripts\python.exe -m video_kb.cli doctor --json
```

Run tests:

```powershell
.venv-video-kb\Scripts\python.exe -m pytest -q
```

## Key Paths

- `src/video_kb/`: pipeline source
- `src/video_kb/obsidian.py`: simplified Obsidian exporter and relation linking
- `src/video_kb/xmind_export.py`: XMind exporter
- `scripts/`: PowerShell wrappers
- `.agents/skills/bilibili-video-kb/`: reusable Codex skill for video-to-Obsidian/XMind automation
- `tests/`: unit tests
- `docs/VIDEO_KB_AUTOMATION.md`: usage doc
- `.cache/video_kb/`: run artifacts and manifests
- `D:\Document\Win_Obsidian知识库\YYH个人知识库\08 视频知识库`: default vault destination
- `C:\Users\yy198\Desktop\B站视频XMind`: default XMind destination

## Constraints

- Cache artifacts stay outside the Obsidian vault.
- The workflow must still produce useful output without OpenAI.
- Bilibili subtitle availability is unstable, so ASR fallback is mandatory.
- Obsidian should keep only notes plus navigation, not topic/concept/transcript layers.
- The Python `xmind` library saves an incomplete legacy archive by default, so the exporter must repair the package and add `meta.xml` plus `META-INF/manifest.xml` before handing files to the desktop XMind client.
