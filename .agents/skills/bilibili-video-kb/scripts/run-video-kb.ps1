param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$InputValue,
    [string]$VaultRoot = "",
    [string]$XMindRoot = "",
    [switch]$SkipSetup,
    [switch]$SkipOpenAI,
    [switch]$Json,
    [switch]$NoOpenObsidian
)

$ErrorActionPreference = "Stop"

function Resolve-VideoKbRepoRoot {
    param(
        [string]$ScriptDir,
        [string]$WorkingDir
    )

    $candidates = @(
        (Join-Path $ScriptDir "..\\..\\.."),
        $WorkingDir
    )

    foreach ($candidate in $candidates) {
        try {
            $resolved = (Resolve-Path $candidate).Path
        } catch {
            continue
        }

        $runScript = Join-Path $resolved "scripts\\run_video_kb.ps1"
        $cliModule = Join-Path $resolved "src\\video_kb\\cli.py"
        if ((Test-Path $runScript) -and (Test-Path $cliModule)) {
            return $resolved
        }
    }

    throw "Unable to locate the video-kb repository root. Run this script from the repo or keep it inside .agents\\skills\\bilibili-video-kb\\scripts."
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-VideoKbRepoRoot -ScriptDir $ScriptDir -WorkingDir (Get-Location).Path
$SetupScript = Join-Path $RepoRoot "scripts\\setup_video_kb.ps1"
$RunScript = Join-Path $RepoRoot "scripts\\run_video_kb.ps1"
$VenvPython = Join-Path $RepoRoot ".venv-video-kb\\Scripts\\python.exe"

if (-not (Test-Path $RunScript)) {
    throw "Missing canonical runner: $RunScript"
}

if (-not (Test-Path $VenvPython)) {
    if ($SkipSetup) {
        throw "Missing .venv-video-kb and -SkipSetup was provided."
    }
    & $SetupScript
}

$arguments = @{
    InputValue = $InputValue
    OpenObsidian = (-not $NoOpenObsidian)
}

if ($VaultRoot) {
    $arguments.VaultRoot = $VaultRoot
}
if ($XMindRoot) {
    $arguments.XMindRoot = $XMindRoot
}
if ($SkipOpenAI) {
    $arguments.SkipOpenAI = $true
}
if ($Json) {
    $arguments.Json = $true
}
& $RunScript @arguments
