[CmdletBinding()]
param([switch]$SkipFrontend)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'tests' -ScriptName $MyInvocation.MyCommand.Name
try {
    $python=Join-Path $script:RepoRoot '.venv\Scripts\python.exe';if(-not(Test-Path $python)){throw 'Backend environment missing.'}
    Invoke-Checked $python @('-m','ruff','check','agentsec','tests') (Join-Path $script:RepoRoot 'backend')
    Invoke-Checked $python @('-m','pytest','--cov=agentsec','--cov-report=term-missing','--cov-report=json:../logs/tests/backend-coverage.json','--cov-fail-under=80') (Join-Path $script:RepoRoot 'backend')
    if(-not $SkipFrontend){Invoke-Checked npm @('run','lint') (Join-Path $script:RepoRoot 'frontend');Invoke-Checked npm @('run','test') (Join-Path $script:RepoRoot 'frontend');Invoke-Checked npm @('run','build') (Join-Path $script:RepoRoot 'frontend')}
    Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
