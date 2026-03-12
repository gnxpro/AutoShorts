; =========================================================
; GNX Production Studio - Basic Installer
; Main public installer
; Default plan after install: BASIC
; Safe version: compile still works even if seed license file is missing
; =========================================================

#define MyAppName "GNX Production Studio"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "GNX Production"
#define MyAppExeName "GNX Production Studio.exe"

; =========================================================
; EDIT THESE PATHS BEFORE BUILDING
; =========================================================
#define MyAppSourceDir "C:\Users\GenEx\Desktop\AutoShorts\dist\GNX Production Studio"
#define MyAppOutputDir "C:\Users\GenEx\Desktop\AutoShorts\installer_output"
#define MyAppLicenseSeed "C:\Users\GenEx\Desktop\AutoShorts\installer\license_basic.gnxlic"
#define MyAppIconFile "C:\Users\GenEx\Desktop\AutoShorts\assets\icons\app.ico"
#define MyWizardImageFile "C:\Users\GenEx\Desktop\AutoShorts\assets\icons\wizard.bmp"
#define MyWizardSmallImageFile "C:\Users\GenEx\Desktop\AutoShorts\assets\icons\wizard_small.bmp"

[Setup]
AppId={{A3C2B4A8-9F45-4C18-8F2A-9E52C132A771}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir={#MyAppOutputDir}
OutputBaseFilename=GNX_Production_Studio_Setup_Basic
SetupIconFile={#MyAppIconFile}
WizardImageFile={#MyWizardImageFile}
WizardSmallImageFile={#MyWizardSmallImageFile}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=no
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no
DisableDirPage=no
DisableReadyMemo=no
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Dirs]
Name: "{userdocs}\GNX Production"; Flags: uninsneveruninstall
Name: "{userdocs}\GNX Production\Outputs"; Flags: uninsneveruninstall
Name: "{userdocs}\GNX Production\Jobs"; Flags: uninsneveruninstall
Name: "{userdocs}\GNX Production\Temp"; Flags: uninsneveruninstall
Name: "{localappdata}\GNX_PRODUCTION"; Flags: uninsneveruninstall

[Files]
; PyInstaller onedir output
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

#if FileExists(MyAppLicenseSeed)
; Default Basic signed license
; Only written if license does not already exist
Source: "{#MyAppLicenseSeed}"; DestDir: "{localappdata}\GNX_PRODUCTION"; DestName: "license.gnxlic"; Flags: onlyifdoesntexist uninsneveruninstall
#endif

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function LicensePath(): string;
begin
  Result := ExpandConstant('{localappdata}\GNX_PRODUCTION\license.gnxlic');
end;

function AppDataRoot(): string;
begin
  Result := ExpandConstant('{localappdata}\GNX_PRODUCTION');
end;

function DocsRoot(): string;
begin
  Result := ExpandConstant('{userdocs}\GNX Production');
end;

function OutputsPath(): string;
begin
  Result := ExpandConstant('{userdocs}\GNX Production\Outputs');
end;

function JobsPath(): string;
begin
  Result := ExpandConstant('{userdocs}\GNX Production\Jobs');
end;

function TempPath(): string;
begin
  Result := ExpandConstant('{userdocs}\GNX Production\Temp');
end;

procedure EnsureDirSafe(PathValue: string);
begin
  if not DirExists(PathValue) then
    ForceDirectories(PathValue);
end;

procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'This installer will install GNX Production Studio with the default BASIC plan.' + #13#10 +
    'Premium and Business upgrades are activated later by importing a signed license file (.gnxlic).' + #13#10 +
    'The application uses the same executable for all plans.';
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    EnsureDirSafe(DocsRoot());
    EnsureDirSafe(OutputsPath());
    EnsureDirSafe(JobsPath());
    EnsureDirSafe(TempPath());
    EnsureDirSafe(AppDataRoot());
  end;
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
begin
  Result :=
    'Setup is ready to install GNX Production Studio.' + NewLine + NewLine +
    'Installation folder:' + NewLine + MemoDirInfo + NewLine + NewLine +
    'Default user folders that will be prepared:' + NewLine +
    '- ' + DocsRoot() + NewLine +
    '- ' + OutputsPath() + NewLine +
    '- ' + JobsPath() + NewLine +
    '- ' + TempPath() + NewLine + NewLine +
    'AppData folder:' + NewLine +
    '- ' + AppDataRoot() + NewLine + NewLine +
    'License file location:' + NewLine +
    '- ' + LicensePath() + NewLine + NewLine +
    'Expected default plan after install:' + NewLine +
    '- BASIC' + NewLine +
    '- 2 social media accounts' + NewLine +
    '- 2 videos per day' + NewLine +
    '- 60 videos per 30 days' + NewLine +
    '- 480p quality' + NewLine + NewLine +
    'Premium and Business are upgraded later via signed .gnxlic files.';
end;