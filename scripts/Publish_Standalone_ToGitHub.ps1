#Requires -Version 5.1
<#
.SYNOPSIS
  Publish **only** `EEG_EDF_Standalone_Tool/` from the full EEG Paradox repo to a **flat** GitHub repo
  (files appear at the remote `main` root: main.py, gui/, …).

.DESCRIPTION
  Uses `git subtree split`. That requires this folder to exist in **committed** history on your
  current branch — commit changes under `EEG_EDF_Standalone_Tool/` first.

  This does **not** upload `modules_pyqt5/`. The **Simulate** tab still needs that package copied
  beside `main.py` on the flat repo (see README), or users run `main_lite.py` / the Lite build.

.PARAMETER RemoteUrl
  Destination remote (HTTPS or SSH). Default: ElChaderino flat converter repo.

.PARAMETER Branch
  Remote branch to update (default: main).

.PARAMETER Force
  Pass `--force` on push (needed if remote history does not match the subtree branch).

.EXAMPLE
  cd "E:\EEG Paradox 1.0.4\EEG Paradox Viewer v2.9.1"
  .\EEG_EDF_Standalone_Tool\scripts\Publish_Standalone_ToGitHub.ps1 -Force
#>
param(
    [string] $RemoteUrl = "https://github.com/ElChaderino/EEP-Paradox-EDF-CSV-JSON-converter-.git",
    [string] $Branch = "main",
    [switch] $Force
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$prefix = "EEG_EDF_Standalone_Tool"
$splitBranch = "standalone-edf-export"

Push-Location $repoRoot

try {
    $tracked = git ls-files "$prefix/" 2>$null
    if (-not $tracked) {
        Write-Host "Nothing tracked under $prefix/. Commit that folder in this repo first, then re-run." -ForegroundColor Red
        exit 1
    }

    Write-Host "Repo root: $repoRoot" -ForegroundColor Cyan
    Write-Host "Splitting subtree prefix: $prefix -> branch $splitBranch" -ForegroundColor Cyan

    git subtree split --prefix="$prefix" -b $splitBranch
    if ($LASTEXITCODE -ne 0) {
        throw "git subtree split failed (exit $LASTEXITCODE)"
    }

    $pushArgs = @("push", $RemoteUrl, "${splitBranch}:${Branch}")
    if ($Force) {
        $pushArgs += "--force"
    }

    Write-Host "Pushing to $RemoteUrl ($splitBranch -> $Branch)..." -ForegroundColor Cyan
    git @pushArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git push failed (exit $LASTEXITCODE). Try again with -Force if histories are unrelated."
    }

    Write-Host "Done. Remote should show a flat tree (main.py at root)." -ForegroundColor Green
}
finally {
    Pop-Location
}
