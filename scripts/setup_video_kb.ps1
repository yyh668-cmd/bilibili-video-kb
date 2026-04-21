param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

function Test-Python {
    param([string]$Executable, [string[]]$Prefix)

    try {
        & $Executable @Prefix -c "print('ok')" | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Resolve-PythonCommand {
    param([string]$Requested)

    if ($Requested) {
        return @{ Executable = $Requested; Prefix = @() }
    }

    if ($env:VIDEO_KB_PYTHON -and (Test-Python -Executable $env:VIDEO_KB_PYTHON -Prefix @())) {
        return @{ Executable = $env:VIDEO_KB_PYTHON; Prefix = @() }
    }

    if (Test-Python -Executable "py" -Prefix @("-3")) {
        return @{ Executable = "py"; Prefix = @("-3") }
    }

    if (Test-Python -Executable "python" -Prefix @()) {
        return @{ Executable = "python"; Prefix = @() }
    }

    throw "Unable to find a usable Python interpreter. Pass -PythonExe explicitly."
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $RepoRoot ".venv-video-kb"
$PythonCommand = Resolve-PythonCommand -Requested $PythonExe

if (-not (Test-Path $VenvPath)) {
    & $PythonCommand.Executable @($PythonCommand.Prefix + @("-m", "venv", $VenvPath))
}

$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e "$RepoRoot[full]"
& $VenvPython -m video_kb.cli doctor --json

Write-Output "Environment ready: $VenvPython"
