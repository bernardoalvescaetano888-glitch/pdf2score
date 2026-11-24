#define MyAppName "Pdf2Score"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Pdf2Score"
#define MyAppURL "https://github.com/bernardoalvescaetano888-glitch/pdf2score"
#define MyAppExeName "Pdf2Score.exe"
#define BuildArch "arm64"

[Setup]
AppId={{A7E4C1D2-3B6F-4E88-9F21-5D0C7B4A1E93}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=AVISO.txt
OutputDir=..\setup
OutputBaseFilename=Pdf2Score-Setup-{#MyAppVersion}-{#BuildArch}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; DestName: "LEIAME.md"; Flags: ignoreversion
Source: "AVISO.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Leia-me"; Filename: "{app}\LEIAME.md"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName} agora"; Flags: nowait postinstall skipifsilent

[Code]
function JavaInstalled(): Boolean;
begin
  Result :=
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\JavaSoft\JRE') or
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\JavaSoft\JDK') or
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Eclipse Adoptium\JDK') or
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\WOW6432Node\JavaSoft\JRE') or
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\WOW6432Node\JavaSoft\JDK');
end;

function MuseScoreInstalled(): Boolean;
begin
  Result :=
    FileExists(ExpandConstant('{pf}\MuseScore 4\bin\mscore.exe')) or
    FileExists(ExpandConstant('{pf32}\MuseScore 4\bin\mscore.exe')) or
    FileExists(ExpandConstant('{pf}\MuseScore 3\bin\mscore.exe')) or
    FileExists(ExpandConstant('{pf32}\MuseScore 3\bin\mscore.exe'));
end;

function ArchitectureName(): string;
begin
  case ProcessorArchitecture of
    paX86: Result := 'x86';
    paX64: Result := 'x64';
    paArm32: Result := 'ARM32';
    paArm64: Result := 'ARM64';
  else
    Result := 'desconhecida';
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if ProcessorArchitecture <> paArm64 then
    Result := MsgBox(
      'ATENÇÃO: este Pdf2Score.exe foi compilado para Windows ARM64.' + #13#10 +
      'Em um Windows ' + ArchitectureName() + ' ele pode não executar.' + #13#10 +
      'Deseja continuar com a instalação mesmo assim?',
      mbConfirmation, MB_YESNO) = IDYES;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Msg: string;
begin
  if CurStep = ssPostInstall then
  begin
    Msg := '';
    if not JavaInstalled then
      Msg := Msg + '- Java 17+ nao detectado (necessario para o Audiveris).' + #13#10;
    if not MuseScoreInstalled then
      Msg := Msg + '- MuseScore 4 nao detectado (necessario para gerar MP3).' + #13#10;
    if Msg <> '' then
      MsgBox(
        'Dependencias externas' + #13#10#13#10 + Msg + #13#10 +
        'O proprio Pdf2Score pode instalar o Audiveris: aba Configuracoes > ' +
        '"Instalar Audiveris agora".', mbInformation, MB_OK);
  end;
end;
