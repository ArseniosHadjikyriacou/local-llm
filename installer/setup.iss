; LocalLLM Inno Setup Script
; Requires Inno Setup 6+ (https://jrsoftware.org/isinfo.php)

[Setup]
AppName=LocalLLM
AppVersion=1.0.0
AppPublisher=LocalLLM
DefaultDirName={autopf}\LocalLLM
DefaultGroupName=LocalLLM
OutputBaseFilename=LocalLLM-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Uncomment and set path if you have an icon:
; SetupIconFile=..\launcher\resources\icon.ico

[Files]
Source: "..\dist\LocalLLM.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\docker-compose.yml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\.env"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LocalLLM"; Filename: "{app}\LocalLLM.exe"
Name: "{autodesktop}\LocalLLM"; Filename: "{app}\LocalLLM.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\LocalLLM.exe"; Description: "Launch LocalLLM"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop containers before uninstalling
Filename: "docker"; Parameters: "compose -f ""{app}\docker-compose.yml"" down"; Flags: runhidden waituntilterminated

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Clean up app data directory
    DelTree(ExpandConstant('{localappdata}\LocalLLM'), True, True, True);
  end;
end;
