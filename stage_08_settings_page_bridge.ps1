$ErrorActionPreference = "Stop"

# ==============================
# CONFIG
# ==============================
$ProjectRoot = "C:\Users\GenEx\Desktop\AutoShorts"
$BackupRoot  = "C:\Users\GenEx\Desktop\AutoShorts\_BACKUP_SYSTEM_LAMA"

$Stamp       = Get-Date -Format "yyyyMMdd_HHmmss"
$StageRoot   = Join-Path $BackupRoot "stage_08_settings_page_bridge_$Stamp"
$UiBackup    = Join-Path $StageRoot "ui_snapshot"
$CoreBackup  = Join-Path $StageRoot "core_snapshot"
$CfgBackup   = Join-Path $StageRoot "config_snapshot"
$LogFile     = Join-Path $StageRoot "settings_page_bridge_log.txt"

# ==============================
# HELPERS
# ==============================
function Ensure-Dir {
	param([string]$Path)
	if (-not (Test-Path $Path)) {
		New-Item -ItemType Directory -Path $Path -Force | Out-Null
	}
}

function Write-Log {
	param([string]$Text)
	$Text | Tee-Object -FilePath $LogFile -Append
}

function Ensure-File {
	param(
		[string]$Path,
		[string]$Content = ""
	)

	$Parent = Split-Path $Path -Parent
	if ($Parent) {
		Ensure-Dir $Parent
	}

	Set-Content -Path $Path -Value $Content -Encoding UTF8
	Write-Log "[WRITE FILE] $Path"
}

function Backup-PathItem {
	param(
		[string]$SourcePath,
		[string]$DestinationDir
	)

	if (Test-Path $SourcePath) {
		Ensure-Dir $DestinationDir
		Copy-Item -Path $SourcePath -Destination $DestinationDir -Recurse -Force
		Write-Log "[BACKUP] $SourcePath"
	}
	else {
		Write-Log "[SKIP]   $SourcePath (not found)"
	}
}

function Is-PlaceholderOrSmallFile {
	param(
		[string]$Path,
		[int]$MaxBytes = 256
	)

	if (-not (Test-Path $Path)) {
		return $true
	}

	$item = Get-Item $Path
	return ($item.Length -le $MaxBytes)
}

function Write-IfMissingOrSmall {
	param(
		[string]$Path,
		[string]$Content,
		[int]$MaxBytes = 256
	)

	if ((-not (Test-Path $Path)) -or (Is-PlaceholderOrSmallFile -Path $Path -MaxBytes $MaxBytes)) {
		Ensure-File -Path $Path -Content $Content
	}
	else {
		Write-Log "[KEEP FILE] $Path already has real content"
	}
}

function Ensure-PackageInit {
	param([string]$FolderPath)

	Ensure-Dir $FolderPath
	$InitFile = Join-Path $FolderPath "__init__.py"
	if (-not (Test-Path $InitFile)) {
		Set-Content -Path $InitFile -Value "" -Encoding UTF8
		Write-Log "[CREATE INIT] $InitFile"
	}
}

# ==============================
# PREPARE
# ==============================
Ensure-Dir $BackupRoot
Ensure-Dir $StageRoot
Ensure-Dir $UiBackup
Ensure-Dir $CoreBackup
Ensure-Dir $CfgBackup

"==== STAGE 08 - SETTINGS PAGE BRIDGE ====" | Out-File $LogFile -Encoding UTF8
Write-Log "ProjectRoot : $ProjectRoot"
Write-Log "BackupRoot  : $BackupRoot"
Write-Log "StageRoot   : $StageRoot"
Write-Log "Time        : $(Get-Date)"
Write-Log ""

# ==============================
# FIND LATEST LEGACY PAGES PACKAGE
# ==============================
$UiRoot = Join-Path $ProjectRoot "ui"
$LegacyPagePackage = $null

if (Test-Path $UiRoot) {
	$LegacyPageDirs = Get-ChildItem -Path $UiRoot -Directory | Where-Object { $_.Name -like "pages_legacy_*" } | Sort-Object Name -Descending
	if ($LegacyPageDirs.Count -gt 0) {
		$LegacyPagePackage = $LegacyPageDirs[0].Name
		Write-Log "[LEGACY PAGES] using $LegacyPagePackage"
	}
	else {
		Write-Log "[LEGACY PAGES] not found"
	}
}

Write-Log ""

# ==============================
# BACKUP
# ==============================
Write-Log "---- BACKUP UI ----"
$UiItems = @(
	"ui\pages",
	"ui\components",
	"ui\theme"
)

foreach ($item in $UiItems) {
	$FullPath = Join-Path $ProjectRoot $item
	Backup-PathItem -SourcePath $FullPath -DestinationDir $UiBackup
}

if ($LegacyPagePackage) {
	Backup-PathItem -SourcePath (Join-Path $ProjectRoot ("ui\" + $LegacyPagePackage)) -DestinationDir $UiBackup
}

Write-Log ""
Write-Log "---- BACKUP CORE ----"
$CoreItems = @(
	"core\ui_blueprint"
)

foreach ($item in $CoreItems) {
	$FullPath = Join-Path $ProjectRoot $item
	Backup-PathItem -SourcePath $FullPath -DestinationDir $CoreBackup
}

Write-Log ""
Write-Log "---- BACKUP CONFIG ----"
$CfgItems = @(
	"config\app_paths.py",
	"config\config_manager.py"
)

foreach ($item in $CfgItems) {
	$FullPath = Join-Path $ProjectRoot $item
	Backup-PathItem -SourcePath $FullPath -DestinationDir $CfgBackup
}

Write-Log ""

# ==============================
# ENSURE STRUCTURE
# ==============================
Write-Log "---- ENSURE STRUCTURE ----"

Ensure-PackageInit (Join-Path $ProjectRoot "core")
Ensure-PackageInit (Join-Path $ProjectRoot "core\ui_blueprint")
Ensure-PackageInit (Join-Path $ProjectRoot "ui")
Ensure-PackageInit (Join-Path $ProjectRoot "ui\pages")
Ensure-PackageInit (Join-Path $ProjectRoot "ui\components")

Write-Log ""

# ==============================
# CONTENT: core/ui_blueprint/page_specs.py
# ==============================
$PageSpecsContent = @'
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any