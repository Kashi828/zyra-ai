[CmdletBinding()]
param(
  [switch]$Json,
  [switch]$SkipNpmInstall
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host 'ZYRA AI - Windows beta preparation' -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw 'Python was not found on PATH. Install Python 3.11+ and rerun this script.'
}

python scripts/bootstrap_windows.py --json:$Json
if ($LASTEXITCODE -ne 0) {
  throw 'Required runtime checks failed. No packages were installed automatically.'
}

if (-not $SkipNpmInstall) {
  if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'npm was not found on PATH. Install Node.js 20+ and rerun.'
  }
  npm install
  if ($LASTEXITCODE -ne 0) { throw 'npm install failed.' }
}

Write-Host 'Beta preparation complete. Build with: npm run build:win' -ForegroundColor Green
