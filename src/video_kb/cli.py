from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from .config import RuntimeConfig
from .obsidian import write_obsidian_package
from .pipeline import PipelineError, build_manifest, run_ingest
from .utils import write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="video-kb", description="Bilibili-first video knowledge extraction pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Process a video URL or local media file.")
    ingest.add_argument("input_value", help="Bilibili URL or local media path.")
    ingest.add_argument("--vault-root", help="Override Obsidian vault root.")
    ingest.add_argument("--cache-root", help="Override cache root.")
    ingest.add_argument("--xmind-root", help="Override desktop XMind export folder.")
    ingest.add_argument("--language", default="zh", help="Primary transcript language. Default: zh")
    ingest.add_argument("--whisper-model", default="small", help="Whisper model size for ASR fallback.")
    ingest.add_argument("--openai-model", default="gpt-4.1-mini", help="OpenAI model for note extraction.")
    ingest.add_argument("--openai-backend", choices=["auto", "openai", "extractive"], default="auto")
    ingest.add_argument("--skip-openai", action="store_true", help="Force extractive note generation.")
    ingest.add_argument("--open-obsidian", action="store_true", help="Open the generated note in Obsidian.")
    ingest.add_argument("--json", action="store_true", help="Print the final manifest as JSON.")

    doctor = subparsers.add_parser("doctor", help="Check runtime dependencies and expected paths.")
    doctor.add_argument("--vault-root", help="Override Obsidian vault root.")
    doctor.add_argument("--cache-root", help="Override cache root.")
    doctor.add_argument("--xmind-root", help="Override desktop XMind export folder.")
    doctor.add_argument("--json", action="store_true", help="Print doctor output as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "doctor":
        return _doctor(args)
    return _ingest(args)


def _ingest(args: argparse.Namespace) -> int:
    config = RuntimeConfig.from_args(
        vault_root=args.vault_root,
        cache_root=args.cache_root,
        xmind_root=args.xmind_root,
        language=args.language,
        whisper_model=args.whisper_model,
        openai_model=args.openai_model,
        openai_backend=args.openai_backend,
        open_obsidian=args.open_obsidian,
        skip_openai=args.skip_openai or args.openai_backend == "extractive",
    )
    try:
        result = run_ingest(args.input_value, config)
        result.artifact_paths = write_obsidian_package(result, config)
        manifest = build_manifest(result)
        write_json(result.run_dir / "run_manifest.json", manifest)
        if args.open_obsidian:
            _open_in_obsidian(config, Path(result.artifact_paths["main_note"]))
        if args.json:
            sys.stdout.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        else:
            sys.stdout.write(f"Main note: {result.artifact_paths['main_note']}\n")
            sys.stdout.write(f"Index note: {result.artifact_paths['index_note']}\n")
            sys.stdout.write(f"XMind map: {result.artifact_paths['xmind_map']}\n")
            sys.stdout.write(f"Run manifest: {result.run_dir / 'run_manifest.json'}\n")
            if result.warnings:
                sys.stdout.write("Warnings:\n")
                for warning in result.warnings:
                    sys.stdout.write(f"- {warning}\n")
        return 0
    except PipelineError as exc:
        sys.stderr.write(f"[video-kb] {exc}\n")
        return 2


def _doctor(args: argparse.Namespace) -> int:
    config = RuntimeConfig.from_args(vault_root=args.vault_root, cache_root=args.cache_root, xmind_root=args.xmind_root)
    checks = {
        "vault_root": {"path": str(config.vault_root), "exists": config.vault_root.exists()},
        "cache_root": {"path": str(config.cache_root), "exists": config.cache_root.exists()},
        "xmind_root": {"path": str(config.xmind_root), "exists": config.xmind_root.exists()},
        "imports": {},
        "env": {
            "OPENAI_API_KEY": bool(__import__("os").environ.get("OPENAI_API_KEY")),
        },
    }
    for module in ("yt_dlp", "faster_whisper", "yaml", "openai"):
        try:
            __import__(module)
            checks["imports"][module] = True
        except ImportError:
            checks["imports"][module] = False
    if args.json:
        sys.stdout.write(json.dumps(checks, ensure_ascii=False, indent=2) + "\n")
    else:
        sys.stdout.write(json.dumps(checks, ensure_ascii=False, indent=2) + "\n")
    return 0


def _open_in_obsidian(config: RuntimeConfig, note_path: Path) -> None:
    vault_name = config.vault_root.name
    relative = note_path.relative_to(config.vault_root).as_posix()
    uri = f"obsidian://open?vault={quote(vault_name)}&file={quote(relative)}"
    subprocess.Popen(["cmd", "/c", "start", "", uri], shell=False)


if __name__ == "__main__":
    raise SystemExit(main())
