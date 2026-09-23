[Setup]
AppName=园区照片分类助手
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\ImageGroup
DefaultGroupName=园区照片分类助手
OutputBaseFilename=ImageGroup-Setup
ArchitecturesAllowed=x64compatible
PrivilegesRequired=lowest
[Files]
Source: "..\dist\园区照片分类助手\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
[Icons]
Name: "{group}\园区照片分类助手"; Filename: "{app}\园区照片分类助手.exe"
Name: "{autodesktop}\园区照片分类助手"; Filename: "{app}\园区照片分类助手.exe"

