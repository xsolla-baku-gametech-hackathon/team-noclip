$asmPath = "C:\Program Files (x86)\Steam\steamapps\common\Stardew Valley\Stardew Valley.dll"
$bytes = [System.IO.File]::ReadAllBytes($asmPath)
$asm = [System.Reflection.Assembly]::Load($bytes)
$type = $asm.GetType("StardewValley.Menus.GameMenu")

Write-Output "--- Fields ---"
$type.GetFields([System.Reflection.BindingFlags]"Public,NonPublic,Instance,Static") | ForEach-Object { "$($_.Name) ($($_.FieldType.Name))" }

Write-Output "--- Methods ---"
$type.GetMethods([System.Reflection.BindingFlags]"Public,NonPublic,Instance,Static") | Where-Object { $_.Name -like "*tab*" -or $_.Name -like "*page*" -or $_.Name -like "*draw*" -or $_.Name -like "*click*" } | ForEach-Object { "$($_.Name)" }
