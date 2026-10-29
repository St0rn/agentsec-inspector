Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:AgentSecVersion = '1.0.0'
$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

function Initialize-AgentSecLog {
    param([Parameter(Mandatory)][string]$Category, [Parameter(Mandatory)][string]$ScriptName)
    $directory = Join-Path $script:RepoRoot "logs\$Category"
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $script:LogPath = Join-Path $directory "$($ScriptName.Replace('.ps1',''))-$stamp.log"
    "$(Get-Date -Format o) | START | $ScriptName | AgentSec $script:AgentSecVersion" | Set-Content -Encoding UTF8 $script:LogPath
    return $script:LogPath
}

function Write-Step {
    param([string]$Message, [ValidateSet('INFO','OK','WARN','ERROR')][string]$Level = 'INFO')
    $line = "$(Get-Date -Format o) | $Level | $Message"
    Write-Host $line
    if ($script:LogPath) { Add-Content -Encoding UTF8 -Path $script:LogPath -Value $line }
}

function Invoke-Checked {
    param([Parameter(Mandatory)][string]$FilePath, [string[]]$Arguments = @(), [string]$WorkingDirectory = $script:RepoRoot)
    Write-Step "Execute: $FilePath $($Arguments -join ' ')"
    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments 2>&1 | ForEach-Object { Write-Step "  $_" }
        if ($LASTEXITCODE -ne 0) { throw "$FilePath exited with code $LASTEXITCODE" }
    } finally { Pop-Location }
}

function Assert-Windows {
    if ($PSVersionTable.PSEdition -eq 'Core' -and -not $IsWindows) { throw 'This operation requires Windows.' }
}

function Get-AgentSecDataDir {
    if ($env:AGENTSEC_DATA_DIR) { return $env:AGENTSEC_DATA_DIR }
    return (Join-Path $env:LOCALAPPDATA 'AgentSec')
}

function Get-CommandVersion {
    param([string]$Name, [string[]]$Arguments = @('--version'))
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) { return $null }
    try { return ((& $command.Source @Arguments 2>$null | Select-Object -First 1) -as [string]).Trim() } catch { return 'present (version unavailable)' }
}

function Stop-AgentSecProcesses {
    $processes=Get-Process 'AgentSec Inspector','agentsec-backend' -ErrorAction SilentlyContinue
    foreach($process in $processes){if($process.MainWindowHandle -ne 0){[void]$process.CloseMainWindow()}}
    if($processes){Start-Sleep -Seconds 3}
    foreach($process in $processes){if(-not $process.HasExited){Stop-Process -Id $process.Id -Force}}
}

function Complete-AgentSecLog {
    param([int]$ExitCode)
    Write-Step "END | exit_code=$ExitCode" $(if ($ExitCode -eq 0) {'OK'} else {'ERROR'})
}
