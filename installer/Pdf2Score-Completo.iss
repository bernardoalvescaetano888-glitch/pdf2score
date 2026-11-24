#define MyAppName "Pdf2Score"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Pdf2Score"
#define MyAppURL "https://github.com/bernardoalvescaetano888-glitch/pdf2score"
#define MyAppExeName "Pdf2Score.exe"
#define BuildArch "arm64"

#define JavaUrl "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21.1+2/OpenJDK17U-jdk_x64_windows_hotspot_17.0.21.1_2.msi"
#define MuseScoreUrl "https://github.com/musescore/MuseScore/releases/download/v4.7.7/MuseScore-Studio-4.7.7.261109195-x86_64.msi"

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
LicenseFile=AVISO-Completo.txt
OutputDir=..\setup
OutputBaseFilename=Pdf2Score-Setup-Completo-{#MyAppVersion}-{#BuildArch}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes
ArchiveExtraction=enhanced

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; DestName: "LEIAME.md"; Flags: ignoreversion
Source: "AVISO-Completo.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Leia-me"; Filename: "{app}\LEIAME.md"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName} agora"; Flags: nowait postinstall skipifsilent

[Code]
var
  DownloadPage: TDownloadWizardPage;

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
    FileExists(ExpandConstant('{pf}\MuseScore Studio 4\bin\mscore.exe')) or
    FileExists(ExpandConstant('{pf32}\MuseScore Studio 4\bin\mscore.exe')) or
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MuseScore 4') or
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\MuseScore 4');
end;

procedure InitializeWizard;
begin
  DownloadPage := CreateDownloadPage(
    SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), nil);
  DownloadPage.ShowBaseNameInsteadOfUrl := True;
end;

function RunInstaller(const FileName, Params: string; var ErrorCode: Integer): Boolean;
begin
  Result := ShellExec('open', FileName, Params, '', SW_SHOW, ewWaitUntilTerminated, ErrorCode);
end;

function InstallMissingDependencies(): Boolean;
var
  NeedJava, NeedMuse: Boolean;
  JavaFile, MuseFile: string;
  ErrorCode: Integer;
begin
  Result := True;
  NeedJava := not JavaInstalled();
  NeedMuse := not MuseScoreInstalled();

  if (not NeedJava) and (not NeedMuse) then
    Exit;

  DownloadPage.Clear;
  if NeedJava then
    DownloadPage.Add('{#JavaUrl}', 'pdf2score-java17.msi', '');
  if NeedMuse then
    DownloadPage.Add('{#MuseScoreUrl}', 'pdf2score-musescore.msi', '');

  DownloadPage.Show;
  try
    try
      DownloadPage.Download;
    except
      MsgBox('Erro ao baixar dependências: ' + GetExceptionMessage, mbError, MB_OK);
      Result := False;
      Exit;
    end;
  finally
    DownloadPage.Hide;
  end;

  JavaFile := ExpandConstant('{tmp}\pdf2score-java17.msi');
  MuseFile := ExpandConstant('{tmp}\pdf2score-musescore.msi');

  if NeedJava then
  begin
    Log('Instalando Java 17...');
    if (not RunInstaller('msiexec.exe', '/i "' + JavaFile + '" /qn /norestart', ErrorCode)) or
       ((ErrorCode <> 0) and (ErrorCode <> 1641) and (ErrorCode <> 3010)) then
    begin
      MsgBox('Não foi possível instalar o Java 17 (código ' + IntToStr(ErrorCode) + ').', mbError, MB_OK);
      Result := False;
    end;
  end;

  if NeedMuse then
  begin
    Log('Instalando MuseScore Studio 4...');
    if (not RunInstaller('msiexec.exe', '/i "' + MuseFile + '" /qn /norestart', ErrorCode)) or
       ((ErrorCode <> 0) and (ErrorCode <> 1641) and (ErrorCode <> 3010)) then
    begin
      MsgBox('Não foi possível instalar o MuseScore 4 (código ' + IntToStr(ErrorCode) + ').', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  if CurPageID = wpReady then
    Result := InstallMissingDependencies()
  else
    Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Msg: string;
begin
  if CurStep = ssPostInstall then
  begin
    Msg := '';
    if not JavaInstalled then
      Msg := Msg + '- Java 17 nao foi detectado apos a instalacao.' + #13#10;
    if not MuseScoreInstalled then
      Msg := Msg + '- MuseScore 4 nao foi detectado apos a instalacao.' + #13#10;
    if Msg <> '' then
      MsgBox('Verifique as dependencias:' + #13#10#13#10 + Msg, mbInformation, MB_OK);
  end;
end;
