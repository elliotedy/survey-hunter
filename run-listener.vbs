' Survey Hunter - hidden auto-start for bot_listener.py
' Runs invisible in the background; writes output to config\listener.log
Option Explicit
Dim sh, fso, dir, cfgDir
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
cfgDir = dir & "\config"
If Not fso.FolderExists(cfgDir) Then fso.CreateFolder(cfgDir)
sh.Run "cmd /c python bot_listener.py >> config\listener.log 2>&1", 0, False
