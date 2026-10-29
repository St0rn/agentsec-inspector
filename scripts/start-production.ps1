[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name
try {
    Assert-Windows
    $candidates=@((Join-Path $env:LOCALAPPDATA 'Programs\AgentSec Inspector\AgentSec Inspector.exe'),(Join-Path $env:ProgramFiles 'AgentSec Inspector\AgentSec Inspector.exe'))
    $app=$candidates|Where-Object{Test-Path $_}|Select-Object -First 1
    if(-not $app){throw 'AgentSec Inspector is not installed. Run install.ps1 or the generated installer.'}
    $process=Start-Process -FilePath $app -PassThru
    Start-Sleep -Seconds 2
    if($process.HasExited){throw "Application exited early with code $($process.ExitCode)."}
    Write-Step "Application started (PID $($process.Id))." 'OK';Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
