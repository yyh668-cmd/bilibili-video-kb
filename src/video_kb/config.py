from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VAULT_ROOT = Path(r"D:\Document\Win_Obsidian知识库\YYH个人知识库")
DEFAULT_KB_ROOT = DEFAULT_VAULT_ROOT / "08 视频知识库"
DEFAULT_CACHE_ROOT = REPO_ROOT / ".cache" / "video_kb"
DEFAULT_XMIND_ROOT = Path.home() / "Desktop" / "B站视频XMind"


@dataclass(slots=True)
class RuntimeConfig:
    repo_root: Path = REPO_ROOT
    vault_root: Path = DEFAULT_VAULT_ROOT
    kb_root: Path = DEFAULT_KB_ROOT
    cache_root: Path = DEFAULT_CACHE_ROOT
    xmind_root: Path = DEFAULT_XMIND_ROOT
    language: str = "zh"
    whisper_model: str = "small"
    openai_model: str = "gpt-4.1-mini"
    openai_backend: str = "auto"
    open_obsidian: bool = False
    skip_openai: bool = False

    @property
    def knowledge_notes_root(self) -> Path:
        return self.kb_root / "01 知识笔记"

    @property
    def navigation_root(self) -> Path:
        return self.kb_root / "02 索引导航"

    @property
    def index_note(self) -> Path:
        return self.navigation_root / "总索引.md"

    @classmethod
    def from_args(
        cls,
        *,
        vault_root: str | None = None,
        cache_root: str | None = None,
        xmind_root: str | None = None,
        language: str | None = None,
        whisper_model: str | None = None,
        openai_model: str | None = None,
        openai_backend: str | None = None,
        open_obsidian: bool = False,
        skip_openai: bool = False,
    ) -> "RuntimeConfig":
        vault = Path(vault_root) if vault_root else DEFAULT_VAULT_ROOT
        cache = Path(cache_root) if cache_root else DEFAULT_CACHE_ROOT
        xmind = Path(xmind_root) if xmind_root else DEFAULT_XMIND_ROOT
        return cls(
            vault_root=vault,
            kb_root=vault / "08 视频知识库",
            cache_root=cache,
            xmind_root=xmind,
            language=language or os.environ.get("VIDEO_KB_LANGUAGE", "zh"),
            whisper_model=whisper_model or os.environ.get("VIDEO_KB_WHISPER_MODEL", "small"),
            openai_model=openai_model or os.environ.get("VIDEO_KB_OPENAI_MODEL", "gpt-4.1-mini"),
            openai_backend=openai_backend or os.environ.get("VIDEO_KB_OPENAI_BACKEND", "auto"),
            open_obsidian=open_obsidian,
            skip_openai=skip_openai,
        )
