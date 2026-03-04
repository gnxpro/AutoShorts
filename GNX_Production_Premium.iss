#define MyAppName "GNX PRO - AI STUDIO"
#define MyAppPublisher "GENERAL EXPLORER PRODUCTION"
#define MyAppURL "https://www.instagram.com/genexproduction/"
#define MyAppExeName "GNX_Production.exe"
#define MyAppVersion "1.0.0"

; Root folder of this .iss (always correct)
#define RootDir SourcePath

[Setup]
AppId={{A5C4E0D2-1D2B-4C2B-9F9B-7A2F1A9F0A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

DisableProgramGroupPage=yes

; Output always goes to <project>\release
OutputDir={#RootDir}release
OutputBaseFilename=GNX_Production_Premium_Setup
Compression=lzma2
SolidCompression=yes

SetupIconFile={#RootDir}assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

ChangesEnvironment=no
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
Name: "startmenuicon"; Description: "Create Start Menu shortcuts"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Files]
; ✅ Always copy from <project>\dist\GNX_Production\*
Source: "{#RootDir}dist\GNX_Production\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Dirs]
Name: "{localappdata}\GNX_PRODUCTION"; Flags: uninsneveruninstall