param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$InputValue,
    [string]$VaultRoot = "",
    [string]$XMindRoot = "",
    [string]$Language = "zh",
    [string]$WhisperModel = "small",
    [string]$OpenAIModel = "gpt-4.1-mini",
    [ValidateSet("auto", "openai", "extractive")]
    [string]$OpenAIBackend = "auto",
    [switch]$SkipOpenAI,
    [switch]$OpenObsidian = $true,
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepoRoot ".venv-video-kb\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Missing .venv-video-kb. Run scripts/setup_video_kb.ps1 first."
}

$Arguments = @(
    "-m", "video_kb.cli", "ingest",
    $InputValue,
    "--language", $Language,
    "--whisper-model", $WhisperModel,
    "--openai-model", $OpenAIModel,
    "--openai-backend", $OpenAIBackend
)

if ($VaultRoot) {
    $Arguments += @("--vault-root", $VaultRoot)
}
if ($XMindRoot) {
    $Arguments += @("--xmind-root", $XMindRoot)
}
if ($SkipOpenAI) {
    $Arguments += "--skip-openai"
}
if ($OpenObsidian) {
    $Arguments += "--open-obsidian"
}
if ($Json) {
    $Arguments += "--json"
}

& $VenvPython @Arguments
