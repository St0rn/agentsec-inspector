[CmdletBinding()]
param([string]$DataDir)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name
try {
    if(-not $DataDir){$DataDir=Get-AgentSecDataDir}
    New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
    $env:AGENTSEC_DATA_DIR=$DataDir
    $python=Join-Path $script:RepoRoot '.venv\Scripts\python.exe';if(-not(Test-Path $python)){throw 'Backend virtual environment is missing.'}
    Invoke-Checked $python @('-c','from agentsec.database import migrate_db; from agentsec.main import seed_scenarios; migrate_db(); seed_scenarios(); print("database migrated")') (Join-Path $script:RepoRoot 'backend')
    $db=Join-Path $DataDir 'agentsec.db';if(-not(Test-Path $db)){throw 'Database was not created.'}
    Write-Step "Database ready at $db" 'OK';Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
