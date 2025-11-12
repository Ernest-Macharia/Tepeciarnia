;~ #AutoIt3Wrapper_Res_File_Add=DpiAwareness.manifest

#include <ButtonConstants.au3>
#include <EditConstants.au3>
#include <GUIConstantsEx.au3>
#include <WindowsConstants.au3>
#include <FileConstants.au3>
#include <MsgBoxConstants.au3>
#include <AutoItConstants.au3>
#include <WinAPIShPath.au3>
#include <GuiComboBox.au3>
#include <Date.au3>
#include <File.au3>
#include <Array.au3>
#include <TrayConstants.au3>
#include "downloadhandler.au3"
; -------------------------
; KODA GUI FORM
; -------------------------
#Region ### START Koda GUI section ### Form=
$form = GUICreate("MP4 Wall", 513, 75, 183, 124, -1, $WS_EX_ACCEPTFILES)
GUISetOnEvent($GUI_EVENT_DROPPED, -1)
$applyb = GUICtrlCreateButton("Apply", 432, 8, 75, 25)
$resetb = GUICtrlCreateButton("Reset", 432, 40, 75, 25)
If ReadIniKey("redResetButton") Then GUICtrlSetBkColor($resetb, 0xff7b7b)
$hideb = GUICtrlCreateButton("Hide", 352, 40, 75, 25) ; === CHANGED HIDE BUTTON POSITION ===
$browseb = GUICtrlCreateButton("Browse", 272, 40, 75, 25) ; === MOVED BROWSE BUTTON LEFT ===
$inputPath = GUICtrlCreateInput("", 8, 8, 417, 25)
$comboScreens = GUICtrlCreateCombo("", 225, 41, 120, 0, $CBS_DROPDOWNLIST)
GUICtrlSetState(-1, $GUI_DROPACCEPTED)
$winStart = GUICtrlCreateCheckbox("Set on windows startup", 8, 40, 137, 25)
Opt("TrayMenuMode", 3)
;~ Opt("TrayOnEventMode", 1)
$tray_show = TrayCreateItem("Show")
$tray_hide = TrayCreateItem("Hide")
$separator = TrayCreateItem("")
$tray_exit = TrayCreateItem("Exit")
TraySetState($TRAY_ICONSTATE_SHOW)
TraySetIcon("\bin\media\icon.ico")

#EndRegion ### END Koda GUI section ###

;~ ---------------------------
;~ CHECK API
;~ ---------------------------
;~ $ifBlocked = Run(@WorkingDir & "\bin\tools\util.exe")
;~ MsgBox($MB_ICONERROR, "Application Error", $ifBlocked)

;~ If not $ifBlocked Then
;~     ConsoleWrite("GG")
;~ Else
;~     MsgBox($MB_ICONERROR, "Application Error", "Unexpected API response. The application cannot start.")
;~     Exit
;~ EndIf

; -------------------------
; AUTORUN LAUCH
; -------------------------
$autoRunState=False
If $CmdLine[0] > 0 Then
	$autoRunState=True
	If $CmdLine[0] > 1 Then
		sleep(2000) ;Time to power others screens
		GUICtrlSetData($inputPath, $CmdLine[1])
	Else
		GUICtrlSetData($inputPath, $CmdLine[1])
		setwallpaper()
		If ReadIniKey("autoPauseFeature") Then Run(@WorkingDir & "\bin\tools\autoPause.exe", "", @SW_HIDE)
	EndIf
	Exit
EndIf

;Detect multiple screen
$multiScreen = ReadIniKey("multiScreenDefault")
If int(_WinAPI_GetSystemMetrics($SM_CMONITORS)) > 1 And ReadIniKey("askMultiScreen") Then
	$aBox = MsgBox(4, "Multi-screen detected", "Do you want run Mp4Wall in multi-screen mode?")
	If $aBox = 6 Then
		$multiScreen = True
	ElseIf $aBox = 7 Then
		$multiScreen = False
	EndIf
EndIf

; -------------------------
; INIT GUI
; -------------------------
GUISetState(@SW_SHOW)
GUICtrlSendMsg($inputPath, $EM_SETCUEBANNER, False, "Browse and select video")
GUICtrlSetState($winStart, $GUI_DISABLE)

If $multiScreen Then ;Init gui multiScreen
	GUICtrlSetState($applyb, $GUI_DISABLE)
	GUICtrlSetState($browseb, $GUI_DISABLE)
	_GUICtrlComboBox_SetItemHeight($comboScreens, 17)
	For $i = 0 To int(_WinAPI_GetSystemMetrics($SM_CMONITORS)) -1
		GUICtrlSetData($comboScreens, "Apply on screen " & $i+1)
	Next
Else
	GUICtrlSetState($comboScreens, $GUI_HIDE)
EndIf


; -------------------------
; GUI LOOP
; -------------------------
While 1
	$nMsg = GUIGetMsg()
	Switch $nMsg
		Case $GUI_EVENT_CLOSE
			Exit
		Case $hideb
            GUISetState(@SW_HIDE)

		Case $applyb
			GUICtrlSetState($applyb, $GUI_DISABLE)
			setwallpaper()
			GUICtrlSetState($applyb, $GUI_ENABLE)
			GUICtrlSetState($winStart, $GUI_ENABLE)
		Case $browseb
			browsefiles()
		case $comboScreens
			GUICtrlSetState($applyb, $GUI_ENABLE)
			GUICtrlSetState($browseb, $GUI_ENABLE)
			GUICtrlSetState($winStart, $GUI_UNCHECKED)
			GUICtrlSetState($winStart, $GUI_DISABLE)
			GUICtrlSetData($inputPath, "")
		Case $winStart
			onWinStart()
		Case $resetb
			reset()
			GUICtrlSetState($winStart, $GUI_DISABLE)
	EndSwitch

	Switch TrayGetMsg()
        Case $tray_show
            GUISetState(@SW_SHOW)

		Case $tray_hide
			GUISetState(@SW_HIDE)

		Case $TRAY_DBLCLICK_PRIMARY
			GUISetState(@SW_SHOW)

        Case $tray_exit
            ; This is the only place the app should exit
            Exit
    EndSwitch
WEnd

; -------------------------
; FUNCTIONS
; -------------------------

Func onWinStart()
	If GUICtrlRead($winStart) = $GUI_CHECKED Then
		$FileName = @WorkingDir & "\Mp4Wall.exe"
		$args = GUICtrlRead($inputPath)

		If $multiScreen Then
			$LinkFileName = @AppDataDir & "\Microsoft\Windows\Start Menu\Programs\Startup\" & "\Mp4Wall"& (_GUICtrlComboBox_GetCurSel($comboScreens)+1)&".lnk"
			$WorkingDirectory = @WorkingDir
			FileCreateShortcut($FileName, $LinkFileName, $WorkingDirectory, '"' & $args & '" '& (_GUICtrlComboBox_GetCurSel($comboScreens)+1), "", "", "", "", @SW_SHOWNORMAL)
		Else
			$LinkFileName = @AppDataDir & "\Microsoft\Windows\Start Menu\Programs\Startup\" & "\Mp4Wall.lnk"
			$WorkingDirectory = @WorkingDir
			FileCreateShortcut($FileName, $LinkFileName, $WorkingDirectory, '"' & $args & '"', "", "", "", "", @SW_SHOWNORMAL)
		EndIf
	Else
		FileDelete(@AppDataDir & "\Microsoft\Windows\Start Menu\Programs\Startup\Mp4Wall.lnk")

		If $multiScreen Then
				FileDelete(@AppDataDir & "\Microsoft\Windows\Start Menu\Programs\Startup\Mp4Wall"&(_GUICtrlComboBox_GetCurSel($comboScreens)+1)&".lnk")
		EndIf

	EndIf
EndFunc   ;==>onWinStart


Func setwallpaper()
	$oldWork = @WorkingDir
	$weebp = @WorkingDir & "\bin\weebp\wp.exe "
	;~ $webview = @WorkingDir & "\bin\tools\webView.exe"
	;~ $mouseWallpaper = ReadIniKey("mouseToWallpaper")
	;~ $forceMouseWallpaper = ReadIniKey("forceMouseToWallpaper")

	$inputUdf = GUICtrlRead($inputPath)
	$nInputPath = DownloadVideoIfURL($inputUdf)
	GUICtrlSetData($inputPath, $nInputPath)
	$inputUdf = GUICtrlRead($inputPath)

	If _WinAPI_UrlIs($inputUdf) == 0 And Not StringRegExp($inputUdf, "\.html?$", 0) And Not ReadIniKey("forceWebview") Then
		killAll()
		FileChangeDir(@WorkingDir & "\bin\mpv\")
		Run($weebp & "run mpv " & '"' & GUICtrlRead($inputPath) & '"' & " --input-ipc-server=\\.\pipe\mpvsocket", "", @SW_HIDE)
		Run($weebp & "add --wait --fullscreen --class mpv", "", @SW_HIDE)

	EndIf
	FileChangeDir($oldWork)
	If @OSVersion = "WIN_11" Or ReadIniKey("forceAutorefresh") Then
		Sleep(2000)
   		Run(@WorkingDir & "\bin\tools\refresh.exe" & " 0x" & GetViewId($oldWork), "", @SW_HIDE)
	EndIf
	If ReadIniKey("autoPauseFeature") Then Run(@WorkingDir & "\bin\tools\autoPause.exe", "", @SW_HIDE)

EndFunc   ;==>setwallpaper


Func browsefiles()
	Local Const $sMessage = "Select the video for wallpaper"
	If ReadIniKey("allFilesAllowed") Then
		Local $sFileOpenDialog = FileOpenDialog($sMessage, @WorkingDir & "\VideosHere" & "\", "All Files (*.*)", BitOR($FD_FILEMUSTEXIST, $FD_PATHMUSTEXIST))
	Else
		Local $sFileOpenDialog = FileOpenDialog($sMessage, @WorkingDir & "\VideosHere" & "\", "Videos (*.avi;*.mp4;*.gif;*.mkv;*.webm;*.mts;*.wmv;*.flv;*.mov;*.html;*.mpeg;*.mpg;*.m4v;*.3gp;*.vob;*.ts;*.m2ts;*.divx;*.rm;*.rmvb;*.ogv;*.edl)", BitOR($FD_FILEMUSTEXIST, $FD_PATHMUSTEXIST))
	EndIf

	If @error Then
		FileChangeDir(@ScriptDir)
	Else
		FileChangeDir(@ScriptDir)
		$sFileOpenDialog = StringReplace($sFileOpenDialog, "|", @CRLF)
		GUICtrlSetData($inputPath, $sFileOpenDialog)
		GUICtrlSetState($winStart, $GUI_ENABLE)
		GUICtrlSetState($winStart, $GUI_UNCHECKED)
	EndIf

EndFunc   ;==>browsefiles

Func reset()
    killAll()
	GUICtrlSetState($applyb, $GUI_ENABLE)
    GUICtrlSetState($winStart, $GUI_UNCHECKED)
    GUICtrlSetData($inputPath, "")
EndFunc   ;==>reset


Func killAll()
    Local $aProcesses = ['mpv.exe', 'wp.exe', 'litewebview.exe', 'Win32WebViewHost.exe', 'autopause.exe', 'mousesender.exe']

    For $sProcess In $aProcesses
        Do
            ProcessClose($sProcess)
        Until Not ProcessExists($sProcess)
    Next

    ; Refresh
    Run(@WorkingDir & "\bin\weebp\wp.exe ls", "", @SW_HIDE)
EndFunc   ;==>killAll

Func ReadIniKey($sKey)
    ; Set the file path to the INI file in the working directory
    $sFilePath = @WorkingDir & "\config.ini"
    If Not FileExists($sFilePath) Then Return False

    ; Attempt to read the value of the key
    $sValue = IniRead($sFilePath, "Configurations", $sKey, "NotFound")

    If $sValue == "true" Then
        Return True
    Else
        Return False
    EndIf
EndFunc ;==>ReadIniKey


Func GetViewId($oldWork)
    ; Define the command to list
    Local $sCommand = '"' & $oldWork & "\bin\weebp\wp.exe" & '"' & " ls"
    Local $iPID = Run(@ComSpec & " /c " & $sCommand, "", @SW_HIDE, $STDOUT_CHILD)

    ; Initialize variables to read the output
    Local $sOutput = ""
    Local $sRead
    While 1
        $sRead = StdoutRead($iPID)
        If @error Then ExitLoop
        $sOutput &= $sRead
    WEnd

    ; Try to find a line containing "mpv"
    Local $sMatch = StringRegExp($sOutput, ".*\[(\w+)\].*mpv.*", 1)

    ; If "mpv" is not found, look for "litewebview"
    If @extended = 0 Then
        $sMatch = StringRegExp($sOutput, ".*\[(\w+)\].*litewebview.*", 1)
    EndIf

    ; Check if a valid ID was found
    If IsArray($sMatch) And UBound($sMatch) > 0 Then
        Return $sMatch[0]
    EndIf

    ; If no ID is found, return an error
    Return SetError(1, 0, "0")
EndFunc ;==>GetViewId

