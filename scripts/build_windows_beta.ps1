$ErrorActionPreference = "Stop"
$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $node -or -not $npm) { throw "Node.js and npm are required. Install them manually, then rerun." }
if (-not (Test-Path ".\package.json")) { throw "Run this script from the ZYRA AI project root." }
if (-not $env:ZYRA_RELEASE_CHANNEL) { $env:ZYRA_RELEASE_CHANNEL = "beta" }
npm run diagnostics
if ($LASTEXITCODE -ne 0) { throw "Diagnostics failed." }
npm run bundle:win-runtime
if ($LASTEXITCODE -ne 0) { throw "Windows runtime bundling failed." }
npm run build:win
if ($LASTEXITCODE -ne 0) { throw "Electron Windows packaging failed." }
Write-Host "Windows beta build completed. Check dist\ for the NSIS installer."
