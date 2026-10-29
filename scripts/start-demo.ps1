[CmdletBinding()]
param([int]$Port=8877)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'tests' -ScriptName $MyInvocation.MyCommand.Name
try{$python=Join-Path $script:RepoRoot '.venv\Scripts\python.exe';if(-not(Test-Path $python)){throw 'Run install-dev.ps1 first.'};Write-Step 'Starting CONTROLLED DEMO environment; do not mix its data with client projects.' 'WARN';Invoke-Checked $python @('-m','uvicorn','server:app','--app-dir','demo','--host','127.0.0.1','--port',$Port) $script:RepoRoot;Complete-AgentSecLog 0;exit 0}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
