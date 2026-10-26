; Script de Inno Setup 6 para Aegis Browser
; Compilador: C:\Users\PC\AppData\Local\Programs\Inno Setup 6\ISCC.exe

#define MyAppName "Aegis Browser"
#define MyAppVersion "1.3.5"
#define MyAppPublisher "Aegis Project"
#define MyAppURL "https://github.com/fabian2007oyanedel-dot/aegis"
#define MyAppExeName "Aegis.exe"

[Setup]
AppId={{9B7F1B50-3274-4F98-8F1A-D7C6B7B3AE91}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Aegis Browser
DisableProgramGroupPage=yes
DefaultGroupName={#MyAppName}
OutputDir=..\dist\installer
OutputBaseFilename=Aegis-Setup-v1.3.5
SetupIconFile=..\src\ui\assets\aegis.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "registerbrowser"; Description: "Registrar Aegis Browser como navegador web en Windows"; GroupDescription: "Integración en el Sistema:"

[Files]
Source: "..\dist\Aegis\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\src\ui\assets\aegis.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\aegis.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\aegis.ico"; Tasks: desktopicon

[Registry]
; Registrar en StartMenuInternet (Integración como Navegador Web Predeterminado)
Root: HKCU; Subkey: "Software\Clients\StartMenuInternet\AegisBrowser"; ValueType: string; ValueData: "Aegis Browser"; Flags: uninsdeletekey; Tasks: registerbrowser
Root: HKCU; Subkey: "Software\Clients\StartMenuInternet\AegisBrowser\DefaultIcon"; ValueType: string; ValueData: "{app}\aegis.ico,0"; Flags: uninsdeletekey; Tasks: registerbrowser
Root: HKCU; Subkey: "Software\Clients\StartMenuInternet\AegisBrowser\shell\open\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletekey; Tasks: registerbrowser

; Capacidades del Navegador
Root: HKCU; Subkey: "Software\Clients\StartMenuInternet\AegisBrowser\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Navegador web ultra rápido, privado y seguro sin telemetría de Google."; Flags: uninsdeletekey; Tasks: registerbrowser
Root: HKCU; Subkey: "Software\Clients\StartMenuInternet\AegisBrowser\Capabilities"; ValueType: string; ValueName: "ApplicationIcon"; ValueData: "{app}\aegis.ico,0"; Flags: uninsdeletekey; Tasks: registerbrowser
Root: HKCU; Subkey: "Software\Clients\StartMenuInternet\AegisBrowser\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "Aegis Browser"; Flags: uninsdeletekey; Tasks: registerbrowser

; Asociaciones de URL (http / https)
Root: HKCU; Subkey: "Software\Clients\StartMenuInternet\AegisBrowser\Capabilities\URLAssociations"; ValueType: string; ValueName: "http"; ValueData: "AegisHTML"; Flags: uninsdeletekey; Tasks: registerbrowser
Root: HKCU; Subkey: "Software\Clients\StartMenuInternet\AegisBrowser\Capabilities\URLAssociations"; ValueType: string; ValueName: "https"; ValueData: "AegisHTML"; Flags: uninsdeletekey; Tasks: registerbrowser

; Registrar la aplicación registrada
Root: HKCU; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "AegisBrowser"; ValueData: "Software\Clients\StartMenuInternet\AegisBrowser\Capabilities"; Flags: uninsdeletevalue; Tasks: registerbrowser

; Tipo de archivo AegisHTML
Root: HKCU; Subkey: "Software\Classes\AegisHTML"; ValueType: string; ValueData: "Documento HTML de Aegis"; Flags: uninsdeletekey; Tasks: registerbrowser
Root: HKCU; Subkey: "Software\Classes\AegisHTML\DefaultIcon"; ValueType: string; ValueData: "{app}\aegis.ico,0"; Flags: uninsdeletekey; Tasks: registerbrowser
Root: HKCU; Subkey: "Software\Classes\AegisHTML\shell\open\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: registerbrowser

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
