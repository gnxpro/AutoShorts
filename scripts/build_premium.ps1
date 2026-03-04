param(
  [string]$SpecFile = "GNX_Production.spec",
  [string]$IssFile  = "GNX_Production_Premium.iss"
)

$ErrorActionPreference = "Stop"

Write-Host "== GNX Premium Build ==" -ForegroundColor Cyan

# Resolve project root from script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $ProjectRoot

Write-Host "ProjectRoot: $ProjectRoot" -ForegroundColor DarkGray

# Activate venv if exists
if (Test-Path ".\venv\Scripts\Activate.ps1") {
  . .\venv\Scripts\Activate.ps1
} elseif (Test-Path ".\.venv\Scripts\Activate.ps1") {
  . .\.venv\Scripts\Activate.ps1
}

# Install deps
python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt | Out-Null
pip install pyinstaller | Out-Null

# Clean
powershell -ExecutionPolicy Bypass -File ".\scripts\clean_release.ps1"

# Build PyInstaller
Write-Host "Building with PyInstaller..." -ForegroundColor Yellow
pyinstaller $SpecFile --noconfirm

# Validate dist output
$ExePath = ".\dist\GNX_Production\GNX_Production.exe"
if (!(Test-Path $ExePath)) {
  Write-Host "ERROR: PyInstaller output not found: $ExePath" -ForegroundColor Red
  Write-Host "Check PyInstaller logs above. Build must produce dist\GNX_Production\GNX_Production.exe" -ForegroundColor Red
  exit 1
}

# Ensure release folder
if (!(Test-Path ".\release")) { New-Item -ItemType Directory -Path ".\release" | Out-Null }

# Find ISCC
$Candidates = @(
  "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
  "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
)

$ISCC = $null
foreach ($c in $Candidates) {
  if (Test-Path $c) { $ISCC = $c; break }
}

if (-not $ISCC) {
  # Try PATH
  $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
  if ($cmd) { $ISCC = $cmd.Source }
}

if (-not $ISCC) {
  Write-Host "ERROR: ISCC.exe not found. Install Inno Setup 6." -ForegroundColor Red
  exit 1
}

Write-Host "ISCC: $ISCC" -ForegroundColor DarkGray

# Compile installer
Write-Host "Compiling installer (Inno Setup)..." -ForegroundColor Yellow
& $ISCC (Join-Path $ProjectRoot $IssFile)

if ($LASTEXITCODE -ne 0) {
  Write-Host "ERROR: Inno Setup compile failed (exit code $LASTEXITCODE)." -ForegroundColor Red
  Write-Host "Most common causes: dist folder missing, icon missing, wrong paths in .iss." -ForegroundColor Red
  exit 1
}

$InstallerPath = ".\release\GNX_Production_Premium_Setup.exe"
if (!(Test-Path $InstallerPath)) {
  Write-Host "WARNING: Compile returned success, but installer not found: $InstallerPath" -ForegroundColor Yellow
  Write-Host "Check OutputDir/OutputBaseFilename in .iss" -ForegroundColor Yellow
} else {
  Write-Host "Installer created: $InstallerPath" -ForegroundColor Green
}

Write-Host "DONE." -ForegroundColor Green