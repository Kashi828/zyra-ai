[CmdletBinding()]
param([switch]$SkipPrepare)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not $SkipPrepare) {
  & (Join-Path $PSScriptRoot 'prepare_windows.ps1')
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

npm run build:win
if ($LASTEXITCODE -ne 0) { throw 'Windows installer build failed.' }

Write-Host 'Installer artifacts are under dist\.' -ForegroundColor Green
Get-ChildItem -Path dist -Filter '*.exe' -ErrorAction SilentlyContinue | Select-Object Name, Length, LastWriteTime
