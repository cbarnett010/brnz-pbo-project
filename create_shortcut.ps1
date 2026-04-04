$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\brnz PBO Project.lnk")
$Shortcut.TargetPath = "C:\brnzpboproject\launch.bat"
$Shortcut.WorkingDirectory = "C:\brnzpboproject"
$Shortcut.WindowStyle = 7
$Shortcut.Description = "brnz PBO Project"
$Shortcut.Save()
