$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\brnz Server Tools.lnk")
$Shortcut.TargetPath = Join-Path $PSScriptRoot "launch.bat"
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.WindowStyle = 7
$Shortcut.Description = "brnz Server Tools"
$Shortcut.Save()
