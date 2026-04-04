$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\brnz Server Tools.lnk")
$Shortcut.TargetPath = "C:\brnzpboproject\launch.bat"
$Shortcut.WorkingDirectory = "C:\brnzpboproject"
$Shortcut.WindowStyle = 7
$Shortcut.Description = "brnz Server Tools"
$Shortcut.Save()
