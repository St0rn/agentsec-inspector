[CmdletBinding()]
param([int]$Port=8765)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'tests' -ScriptName $MyInvocation.MyCommand.Name
try {
    $python=Join-Path $script:RepoRoot '.venv\Scripts\python.exe';if(-not(Test-Path $python)){throw 'Run install-dev.ps1 first.'}
    if(-not $env:AGENTSEC_API_TOKEN){$env:AGENTSEC_API_TOKEN=[guid]::NewGuid().ToString('N')+[guid]::NewGuid().ToString('N')}
    $env:AGENTSEC_PORT=$Port;$env:VITE_API_TOKEN=$env:AGENTSEC_API_TOKEN;$env:VITE_API_URL="http://127.0.0.1:$Port"
    $backend=Start-Process -FilePath $python -ArgumentList @('-m','uvicorn','agentsec.main:app','--app-dir','backend','--host','127.0.0.1','--port',$Port) -WorkingDirectory $script:RepoRoot -PassThru
    try {Start-Sleep -Seconds 2;Invoke-Checked npm @('run','dev') (Join-Path $script:RepoRoot 'frontend')} finally {if(-not $backend.HasExited){Stop-Process -Id $backend.Id -Force}}
    Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
