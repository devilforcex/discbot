; ============================================================
;  DiscBot — Inno Setup installer script
;  ------------------------------------------------------------
;  Builds a Windows setup.exe that:
;    - Installs the bot to E:\discbot (fixed native Windows path)
;    - Creates Start Menu + Desktop shortcuts to start.bat / stop.bat
;    - Optionally runs first-time setup after install
;
;  Requirements:
;    - Inno Setup 6+ : https://jrsoftware.org/isinfo.php
;    - Python 3.12+ and Java 17+ must be installed by the user
;      (the installer checks and links to the downloads)
;
;  Build:
;    1. Zip the repo contents (bot/, requirements.txt, .env.example, etc.)
;       alongside this .iss or just run ISCC from the repo root.
;    2. Open DiscBot.iss in Inno Setup → Compile → produces Output\DiscBotSetup.exe
; ============================================================

#define MyAppName "DiscBot"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Steel / devilforcex"
#define MyAppURL "https://github.com/devilforcex/discbot"
#define MyAppExeName "start.bat"

[Setup]
AppId={{B5C3E4F1-9A82-4D7F-B2C6-111111111111}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName=E:\discbot
DefaultGroupName=DiscBot
AllowNoIcons=yes
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=DiscBotSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "bulgarian"; MessagesFile: "compiler:Languages\Bulgarian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "runsetup"; Description: "Launch first-time setup after install"; GroupDescription: "Post-install:"; Flags: checkedonce

[Files]
; Project source files
Source: "..\..\bot\*"; DestDir: "{app}\bot"; Flags: recursesubdirs createallsubdirs
Source: "..\..\docs\*"; DestDir: "{app}\docs"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\tests\*"; DestDir: "{app}\tests"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\..\requirements.txt"; DestDir: "{app}"
Source: "..\..\.env.example"; DestDir: "{app}"
Source: "..\..\application.yml.example"; DestDir: "{app}"
Source: "..\..\README.md"; DestDir: "{app}"
Source: "..\..\install.bat"; DestDir: "{app}"
Source: "..\..\start.bat"; DestDir: "{app}"
Source: "..\..\docs\PROJECT_PLAN.md"; DestDir: "{app}\docs"; Flags: skipifsourcedoesntexist

; Windows scripts
Source: "setup.bat"; DestDir: "{app}\scripts\windows"
Source: "start.bat"; DestDir: "{app}\scripts\windows"
Source: "stop.bat"; DestDir: "{app}\scripts\windows"
Source: "update.bat"; DestDir: "{app}\scripts\windows"
Source: "install.ps1"; DestDir: "{app}\scripts\windows"
Source: "start.ps1"; DestDir: "{app}\scripts\windows"
Source: "stop.ps1"; DestDir: "{app}\scripts\windows"
Source: "update.ps1"; DestDir: "{app}\scripts\windows"
Source: "README-windows.md"; DestDir: "{app}\scripts\windows"

; NOTE: Lavalink.jar is intentionally NOT bundled — it's large (~80 MB)
; and updated frequently; setup.bat downloads the latest release on first run.

[Icons]
Name: "{group}\Start DiscBot"; Filename: "{app}\scripts\windows\start.bat"; WorkingDir: "{app}"
Name: "{group}\Stop DiscBot"; Filename: "{app}\scripts\windows\stop.bat"; WorkingDir: "{app}"
Name: "{group}\First-time Setup"; Filename: "{app}\scripts\windows\setup.bat"; WorkingDir: "{app}"
Name: "{group}\DiscBot folder"; Filename: "{app}"
Name: "{group}\Uninstall DiscBot"; Filename: "{uninstallexe}"
Name: "{autodesktop}\DiscBot"; Filename: "{app}\scripts\windows\start.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; First-time setup after install (creates venv, downloads Lavalink, opens .env)
Filename: "{app}\scripts\windows\setup.bat"; Description: "Run first-time setup"; Flags: nowait postinstall skipifsilent; Tasks: runsetup

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.venv"
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\.env"
Type: files; Name: "{app}\application.yml"
Type: files; Name: "{app}\Lavalink.jar"
Type: filesandordirs; Name: "{app}\plugins"
