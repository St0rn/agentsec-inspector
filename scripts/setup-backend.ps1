[CmdletBinding()]
param([switch]$ForceRecreate)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name
try {
    $venv=Join-Path $script:RepoRoot '.venv'
    if($ForceRecreate -and (Test-Path $venv)){Remove-Item -Recurse -Force $venv}
    if(-not(Test-Path (Join-Path $venv 'Scripts\python.exe'))){Invoke-Checked python @('-m','venv',$venv)}
    $python=Join-Path $venv 'Scripts\python.exe'
    Invoke-Checked $python @('-m','pip','install','--disable-pip-version-check','--upgrade','pip==25.1.1')
    $lock=Join-Path $script:RepoRoot 'backend\requirements.lock'
    $requirements=if(Test-Path $lock){$lock}else{Join-Path $script:RepoRoot 'backend\requirements-dev.txt'}
    Invoke-Checked $python @('-m','pip','install','--disable-pip-version-check','-r',$requirements)
    Invoke-Checked $python @('-c','import fastapi, sqlalchemy, agentsec') (Join-Path $script:RepoRoot 'backend')
    Complete-AgentSecLog 0; exit 0
} catch {Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
