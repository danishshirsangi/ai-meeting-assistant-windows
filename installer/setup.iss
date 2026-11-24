#define AppName "AI Meeting Assistant"
#ifndef AppVersion
#define AppVersion "1.0.0"
#endif
[Setup]
AppId=AI-Meeting-Assistant-Windows
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\AI Meeting Assistant
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=AI-Meeting-Assistant-{#AppVersion}-x64-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\AI-Meeting-Assistant.exe
CloseApplications=yes
[Files]
Source: "..\dist\AI-Meeting-Assistant\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Icons]
Name: "{group}\AI Meeting Assistant"; Filename: "{app}\AI-Meeting-Assistant.exe"
Name: "{userdesktop}\AI Meeting Assistant"; Filename: "{app}\AI-Meeting-Assistant.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\AI-Meeting-Assistant.exe"; Description: "Launch AI Meeting Assistant"; Flags: nowait postinstall skipifsilent
