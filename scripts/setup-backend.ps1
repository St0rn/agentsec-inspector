[CmdletBinding()]
param([switch]$ForceRecreate)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name
try {
    $venv=Join-Path $script:RepoRoot '.venv'
    if($ForceRecreate -and (Test-Path $venv)){Remove-Item -Recurse -Force $venv}
    $venvPython=Join-Path $venv 'Scripts\python.exe'
    if((Test-Path $venv) -and -not(Test-Path $venvPython)){
        Write-Step "Incomplete virtual environment detected; recreating $venv" 'WARN'
        Remove-Item -LiteralPath $venv -Recurse -Force
    }
    if(Test-Path $venvPython){
        try{[void](Invoke-Checked $venvPython @('-c','import sys; assert sys.prefix != sys.base_prefix'))}
        catch{
            Write-Step "Unusable virtual environment detected; recreating $venv" 'WARN'
            Remove-Item -LiteralPath $venv -Recurse -Force
        }
    }
    if(-not(Test-Path $venvPython)){[void](Invoke-Checked python @('-m','venv',$venv))}
    $python=Join-Path $venv 'Scripts\python.exe'
    [void](Invoke-Checked $python @('-m','pip','install','--disable-pip-version-check','--upgrade','pip==25.1.1'))
    $lock=Join-Path $script:RepoRoot 'backend\requirements.lock'
    $requirements=if(Test-Path $lock){$lock}else{Join-Path $script:RepoRoot 'backend\requirements-dev.txt'}
    [void](Invoke-Checked $python @('-m','pip','install','--disable-pip-version-check','-r',$requirements))
    [void](Invoke-Checked $python @('-c','import fastapi, sqlalchemy, agentsec') (Join-Path $script:RepoRoot 'backend'))
    Complete-AgentSecLog 0; exit 0
} catch {Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
