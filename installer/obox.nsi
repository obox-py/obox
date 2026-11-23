; obox 安装脚本（由 scripts/build_installer.py 生成）
!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

!define APP_NAME "obox"
!define APP_VERSION "__VERSION__"
!define APP_PUBLISHER "obox"
!define UNINST_ROOT "Software\Microsoft\Windows\CurrentVersion\Uninstall\obox"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "__OUTFILE__"
InstallDir "$PROGRAMFILES64\obox"
RequestExecutionLevel highest
Unicode true
SetCompressor /SOLID lzma

Var InstallMode
Var ScopeExplicit
Var ModeAllRadio
Var ModeCurrentRadio

!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
Page custom ModePage ModePageLeave
!define MUI_PAGE_CUSTOMFUNCTION_PRE DirectoryPre
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\obox.exe"
!define MUI_FINISHPAGE_RUN_TEXT "运行 obox"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

Function .onInit
    SetRegView 64
    StrCpy $InstallMode "all"
    StrCpy $ScopeExplicit 0
    ${GetParameters} $R0
    ${GetOptions} $R0 "/CURRENTUSER" $R1
    ${IfNot} ${Errors}
        StrCpy $InstallMode "current"
        StrCpy $ScopeExplicit 1
    ${EndIf}
    ${GetOptions} $R0 "/ALLUSERS" $R1
    ${IfNot} ${Errors}
        StrCpy $InstallMode "all"
        StrCpy $ScopeExplicit 1
    ${EndIf}
    ${If} $ScopeExplicit == 0
        ReadRegStr $R1 HKCU "Software\obox" "InstallDir"
        ${If} $R1 != ""
            StrCpy $InstallMode "current"
        ${Else}
            ReadRegStr $R1 HKLM "Software\obox" "InstallDir"
            ${If} $R1 != ""
                StrCpy $InstallMode "all"
            ${EndIf}
        ${EndIf}
    ${EndIf}
    Call ApplyMode
    Call CheckAdmin
FunctionEnd

Function DirectoryPre
    ${If} $InstallMode == "current"
        ${If} $INSTDIR == ""
        ${OrIf} $INSTDIR == "$PROGRAMFILES64\obox"
            StrCpy $INSTDIR "$LOCALAPPDATA\Programs\obox"
        ${EndIf}
    ${Else}
        ${If} $INSTDIR == ""
        ${OrIf} $INSTDIR == "$LOCALAPPDATA\Programs\obox"
            StrCpy $INSTDIR "$PROGRAMFILES64\obox"
        ${EndIf}
    ${EndIf}
FunctionEnd

Function ApplyMode
    ${If} $InstallMode == "current"
        SetShellVarContext current
        StrCpy $0 "$LOCALAPPDATA\Programs\obox"
    ${Else}
        SetShellVarContext all
        StrCpy $0 "$PROGRAMFILES64\obox"
    ${EndIf}
    ${If} $INSTDIR == ""
    ${OrIf} $INSTDIR == "$PROGRAMFILES64\obox"
    ${OrIf} $INSTDIR == "$LOCALAPPDATA\Programs\obox"
        StrCpy $INSTDIR $0
    ${EndIf}
FunctionEnd

Function CheckAdmin
    ${If} $InstallMode == "all"
        UserInfo::GetAccountType
        Pop $0
        ${If} $0 != "Admin"
            ${If} ${Silent}
                SetErrorLevel 5
                Quit
            ${Else}
                MessageBox MB_ICONSTOP "为所有用户安装需要管理员权限；请以管理员身份运行，或改选“仅为我安装”。"
                Abort
            ${EndIf}
		${EndIf}
    ${EndIf}
FunctionEnd

Function ModePage
    !insertmacro MUI_HEADER_TEXT "选择安装范围" "为所有用户安装需要管理员权限，仅为我安装不需要。"
    nsDialogs::Create 1018
    Pop $0
    ${NSD_CreateRadioButton} 0 0 100% 14u "为所有用户安装（Program Files）"
    Pop $ModeAllRadio
    ${NSD_CreateRadioButton} 0 20u 100% 14u "仅为我安装（当前用户目录，无需管理员）"
    Pop $ModeCurrentRadio
    ${If} $InstallMode == "current"
        ${NSD_Check} $ModeCurrentRadio
    ${Else}
        ${NSD_Check} $ModeAllRadio
    ${EndIf}
    nsDialogs::Show
FunctionEnd

Function ModePageLeave
    ${NSD_GetState} $ModeCurrentRadio $0
    ${If} $0 == ${BST_CHECKED}
        StrCpy $InstallMode "current"
    ${Else}
        StrCpy $InstallMode "all"
    ${EndIf}
    Call ApplyMode
    Call CheckAdmin
FunctionEnd

Section "obox" SecMain
    SectionIn RO
    SetOutPath "$INSTDIR"
    File /r "__STAGE__\\*.*"

    ${If} $InstallMode == "current"
        WriteRegStr HKCU "Software\obox" "InstallDir" "$INSTDIR"
        WriteRegStr HKCU "Software\obox" "Version" "${APP_VERSION}"
        WriteRegStr HKCU "${UNINST_ROOT}" "DisplayName" "${APP_NAME}"
        WriteRegStr HKCU "${UNINST_ROOT}" "DisplayVersion" "${APP_VERSION}"
        WriteRegStr HKCU "${UNINST_ROOT}" "Publisher" "${APP_PUBLISHER}"
        WriteRegStr HKCU "${UNINST_ROOT}" "InstallLocation" "$INSTDIR"
        WriteRegStr HKCU "${UNINST_ROOT}" "UninstallString" "$INSTDIR\uninstall.exe"
        WriteRegDWORD HKCU "${UNINST_ROOT}" "NoModify" 1
        WriteRegDWORD HKCU "${UNINST_ROOT}" "NoRepair" 1
    ${Else}
        WriteRegStr HKLM "Software\obox" "InstallDir" "$INSTDIR"
        WriteRegStr HKLM "Software\obox" "Version" "${APP_VERSION}"
        WriteRegStr HKLM "${UNINST_ROOT}" "DisplayName" "${APP_NAME}"
        WriteRegStr HKLM "${UNINST_ROOT}" "DisplayVersion" "${APP_VERSION}"
        WriteRegStr HKLM "${UNINST_ROOT}" "Publisher" "${APP_PUBLISHER}"
        WriteRegStr HKLM "${UNINST_ROOT}" "InstallLocation" "$INSTDIR"
        WriteRegStr HKLM "${UNINST_ROOT}" "UninstallString" "$INSTDIR\uninstall.exe"
        WriteRegDWORD HKLM "${UNINST_ROOT}" "NoModify" 1
        WriteRegDWORD HKLM "${UNINST_ROOT}" "NoRepair" 1
    ${EndIf}

    CreateDirectory "$SMPROGRAMS\obox"
    CreateShortcut "$SMPROGRAMS\obox\obox.lnk" "$INSTDIR\obox.exe"
    CreateShortcut "$DESKTOP\obox.lnk" "$INSTDIR\obox.exe"
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
    SetRegView 64
    ReadRegStr $0 HKCU "Software\obox" "InstallDir"
    ReadRegStr $1 HKLM "Software\obox" "InstallDir"
    ${If} $0 == "$INSTDIR"
        SetShellVarContext current
        DeleteRegKey HKCU "Software\obox"
        DeleteRegKey HKCU "${UNINST_ROOT}"
    ${ElseIf} $1 == "$INSTDIR"
        SetShellVarContext all
        DeleteRegKey HKLM "Software\obox"
        DeleteRegKey HKLM "${UNINST_ROOT}"
    ${ElseIf} $1 != ""
        SetShellVarContext all
        DeleteRegKey HKLM "Software\obox"
        DeleteRegKey HKLM "${UNINST_ROOT}"
    ${Else}
        SetShellVarContext current
        DeleteRegKey HKCU "Software\obox"
        DeleteRegKey HKCU "${UNINST_ROOT}"
    ${EndIf}
    Delete "$DESKTOP\obox.lnk"
    Delete "$SMPROGRAMS\obox\obox.lnk"
    RMDir "$SMPROGRAMS\obox"
    RMDir /r "$INSTDIR"
SectionEnd
