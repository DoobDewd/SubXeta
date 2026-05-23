[Setup]
AppName=SubXeta
AppVersion=1.0.0
AppPublisher=DoobDewd
DefaultDirName={autopf}\SubXeta
DefaultGroupName=SubXeta
OutputDir=dist
OutputBaseFilename=SubXeta_Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
MinVersion=10.0
UninstallDisplayIcon={app}\SubtitleGen.exe
SetupIconFile=icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\SubtitleGen\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SubXeta"; Filename: "{app}\SubtitleGen.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,SubXeta}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\SubXeta"; Filename: "{app}\SubtitleGen.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\SubtitleGen.exe"; Description: "{cm:LaunchProgram,SubXeta}"; Flags: nowait postinstall skipifsilent

[Code]
var
  DeleteCache: Boolean;

function InitializeUninstall: Boolean;
begin
  Result := True;
  DeleteCache := MsgBox('Delete cached models?' + #13#13 +
                        'This will free up ~5-8 GB of space.' + #13 +
                        'These will redownload if you use SubXeta again.',
                        mbConfirmation, MB_YESNO) = IDYES;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserProfile: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if DeleteCache then
    begin
      UserProfile := GetEnv('USERPROFILE');
      DelTree(UserProfile + '\.cache\huggingface', True, True, True);
      DelTree(UserProfile + '\.cache\whisper', True, True, True);
      DelTree(UserProfile + '\.cache\torch', True, True, True);
      DelTree(UserProfile + '\.pyannote', True, True, True);
    end;
  end;
end;
