param([Parameter(Mandatory=$true)][string]$Executable)
$ErrorActionPreference = 'Stop'
$target = [System.IO.Path]::GetFullPath($Executable)
$matching = @(Get-Process | Where-Object {
    try { $_.Path -and [System.IO.Path]::GetFullPath($_.Path) -eq $target } catch { $false }
})
if (-not $matching.Count) { exit 0 }
# A normal close lets the application flush its save queue. Never force-kill it.
foreach ($process in $matching) {
    try {
        if (-not $process.HasExited -and $process.MainWindowHandle -ne 0) {
            $null = $process.CloseMainWindow()
        }
    } catch [System.InvalidOperationException] { }
}
$deadline = [DateTime]::UtcNow.AddSeconds(15)
foreach ($process in $matching) {
    $remaining = [int][Math]::Max(0, ($deadline - [DateTime]::UtcNow).TotalMilliseconds)
    try {
        if (-not $process.HasExited -and -not $process.WaitForExit($remaining)) {
            throw 'StroyID is still running. Close it normally, then rebuild. No process was force-stopped.'
        }
    } catch [System.InvalidOperationException] { }
}
