# scripts/fix_git_repo.ps1
$ErrorActionPreference = "Continue"

Write-Host "== GNX Git Repo Fix (remove large files) ==" -ForegroundColor Cyan

# Go to project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $ProjectRoot

# 1) Ensure .gitignore exists and contains required rules
$gi = Join-Path $ProjectRoot ".gitignore"
if (!(Test-Path $gi)) { New-Item -ItemType File -Path $gi | Out-Null }

$rules = @(
"venv/",
".venv/",
"assets/ffmpeg/",
"release/",
"dist/",
"build/",
"outputs/",
"temp*/",
".env",
"*.exe",
"*.dll",
"*.zip",
"*.7z"
)

$existing = @()
try { $existing = Get-Content $gi -ErrorAction SilentlyContinue } catch {}

foreach ($r in $rules) {
    if ($existing -notcontains $r) {
        Add-Content -Path $gi -Value $r
    }
}

Write-Host "[OK] .gitignore updated" -ForegroundColor Green

function TryGitRmCached([string]$path) {
    # only attempt if the path is tracked
    $tracked = git ls-files -- "$path" 2>$null
    if ($tracked) {
        Write-Host "Removing tracked path from index: $path" -ForegroundColor Yellow
        git rm -r --cached -- "$path" 2>$null | Out-Null
    } else {
        Write-Host "Skip (not tracked): $path" -ForegroundColor DarkGray
    }
}

# 2) Remove big folders from git tracking if they are tracked
$pathsToUntrack = @("venv", ".venv", "release", "dist", "build", "outputs", "temp", "temp_download", "temp_downloads", "assets/ffmpeg")
foreach ($p in $pathsToUntrack) { TryGitRmCached $p }

# Also remove any tracked *.exe or *.dll that slipped in
$trackedExe = git ls-files "*.exe" 2>$null
if ($trackedExe) {
    Write-Host "Removing tracked *.exe files from index..." -ForegroundColor Yellow
    git rm --cached -r "*.exe" 2>$null | Out-Null
}
$trackedDll = git ls-files "*.dll" 2>$null
if ($trackedDll) {
    Write-Host "Removing tracked *.dll files from index..." -ForegroundColor Yellow
    git rm --cached -r "*.dll" 2>$null | Out-Null
}

Write-Host "[OK] Index cleanup done" -ForegroundColor Green

# 3) Stage and commit
git add .gitignore | Out-Null

# Stage source folders if present
$sourcePaths = @("core","gnx","pages","ui","scripts","main.py","requirements.txt","GNX_Production.spec","GNX_Production_Premium.iss","README.md",".env.example")
foreach ($sp in $sourcePaths) {
    if (Test-Path $sp) { git add -- $sp 2>$null | Out-Null }
}

$changes = git status --porcelain
if ($changes) {
    git commit -m "Fix: clean repo (source only, ignore build/venv/releases)" | Out-Null
    Write-Host "[OK] Commit created" -ForegroundColor Green
} else {
    Write-Host "[OK] No changes to commit" -ForegroundColor Green
}

Write-Host ""
Write-Host "Now run:" -ForegroundColor Cyan
Write-Host "  git branch -M main" -ForegroundColor Cyan
Write-Host "  git push -u origin main --force" -ForegroundColor Cyan