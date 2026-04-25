param(
[string]$Plan="PREMIUM"
)

Write-Host ""
Write-Host "============================="
Write-Host "GNX PRO BUILD SYSTEM"
Write-Host "PLAN: $Plan"
Write-Host "============================="

# activate venv
if(Test-Path ".\venv\Scripts\Activate.ps1"){
    . .\venv\Scripts\Activate.ps1
}

pip install -r requirements.txt

pip install pyinstaller

Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

Write-Host "Building executable..."

pyinstaller GNX_Production.spec --noconfirm --clean

Write-Host "Compiling installer..."

$ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

& $ISCC installer\GNX_Production_Setup.iss /DPLAN=$Plan

Write-Host ""
Write-Host "BUILD COMPLETE"
Write-Host ""