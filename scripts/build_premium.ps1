param(
  [string]$SpecFile = "GNX_Production.spec",
  [string]$IssFile  = "GNX_Production_Premium.iss"
)

$ErrorActionPreference = "Stop"

Write-Host "== GNX Premium Rebuild ==" -ForegroundColor Cyan

# Resolve project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $ProjectRoot
Write-Host "ProjectRoot: $ProjectRoot" -ForegroundColor DarkGray

# Activate venv
if (Test-Path ".\venv\Scripts\Activate.ps1") {
  . .\venv\Scripts\Activate.ps1
} elseif (Test-Path ".\.venv\Scripts\Activate.ps1") {
  . .\.venv\Scripts\Activate.ps1
} else {
  Write-Host "WARNING: venv not found. Using system python." -ForegroundColor Yellow
}

# Dependencies
python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt | Out-Null
pip install pyinstaller openai pillow openpyxl | Out-Null

# Clean pyinstaller artifacts (keep release/)
Remove-Item -Recurse -Force .\build, .\dist -ErrorAction SilentlyContinue

# Build
Write-Host "Building PyInstaller..." -ForegroundColor Yellow
pyinstaller $SpecFile --noconfirm --clean

# Validate output
$AppExe = ".\dist\GNX_Production\GNX_Production.exe"
$WorkerExe = ".\dist\GNX_Production\gnx_worker.exe"

if (!(Test-Path $AppExe)) {
  Write-Host "ERROR: App EXE not found: $AppExe" -ForegroundColor Red
  exit 1
}
if (!(Test-Path $WorkerExe)) {
  Write-Host "ERROR: Worker EXE not found: $WorkerExe" -ForegroundColor Red
  Write-Host "Fix: ensure spec builds worker (worker_entry.py -> gnx_worker.exe)" -ForegroundColor Red
  exit 1
}

Write-Host "OK: App EXE + Worker EXE ready." -ForegroundColor Green

# Ensure release folder
if (!(Test-Path ".\release")) { New-Item -ItemType Directory -Path ".\release" | Out-Null }

# Find ISCC
$Candidates = @(
  "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
  "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
)

$ISCC = $null
foreach ($c in $Candidates) { if (Test-Path $c) { $ISCC = $c; break } }
if (-not $ISCC) {
  $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
  if ($cmd) { $ISCC = $cmd.Source }
}
if (-not $ISCC) {
  Write-Host "ERROR: ISCC.exe not found. Install Inno Setup 6." -ForegroundColor Red
  exit 1
}

Write-Host "Compiling Premium Installer..." -ForegroundColor Yellow
& $ISCC (Join-Path $ProjectRoot $IssFile)

if ($LASTEXITCODE -ne 0) {
  Write-Host "ERROR: Inno Setup compile failed (exit code $LASTEXITCODE)." -ForegroundColor Red
  exit 1
}

$InstallerPath = ".\release\GNX_Production_Premium_Setup.exe"
if (!(Test-Path $InstallerPath)) {
  Write-Host "WARNING: Installer not found: $InstallerPath" -ForegroundColor Yellow
  exit 1
}

Write-Host "DONE ✅ Installer created: $InstallerPath" -ForegroundColor Green