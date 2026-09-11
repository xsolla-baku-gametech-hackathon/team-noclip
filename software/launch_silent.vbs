Set WshShell = CreateObject("WScript.Shell")
strPath = WScript.ScriptFullName
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objFile = objFSO.GetFile(strPath)
strFolder = objFSO.GetParentFolderName(objFile)
WshShell.CurrentDirectory = strFolder

If objFSO.FileExists(strFolder & "\xsolla_launcher.exe") Then
    WshShell.Run """" & strFolder & "\xsolla_launcher.exe""", 0, False
Else
    WshShell.Run "pythonw.exe main.py", 0, False
End If
