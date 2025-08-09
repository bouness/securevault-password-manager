; main.iss - Inno Setup script for SecureVault

[Setup]
AppName=SecureVault
AppVersion=latest
DefaultDirName={autopf}\SecureVault
DefaultGroupName=SecureVault
OutputDir=installer_output
OutputBaseFilename=SecureVaultInstaller
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\main.exe
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\main.dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SecureVault"; Filename: "{app}\main.exe"
Name: "{commondesktop}\SecureVault"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\main.exe"; Description: "Launch SecureVault"; Flags: nowait postinstall skipifsilent