[CmdletBinding()]
param([string]$DataDir)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'installation' -ScriptName $MyInvocation.MyCommand.Name
try {
    if(-not $DataDir){$DataDir=Get-AgentSecDataDir}
    New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
    $env:AGENTSEC_DATA_DIR=$DataDir
    $python=Join-Path $script:RepoRoot '.venv\Scripts\python.exe';if(-not(Test-Path $python)){throw 'Backend virtual environment is missing or incomplete. Run setup-backend.ps1.'}
    $migrationCode='from agentsec.database import migrate_db; from agentsec.main import seed_scenarios; migrate_db(); seed_scenarios()'
    [void](Invoke-Checked $python @('-c',$migrationCode) (Join-Path $script:RepoRoot 'backend'))
    $db=Join-Path $DataDir 'agentsec.db';if(-not(Test-Path $db)){throw 'Database was not created.'}
    $integrityCode='import sqlite3,sys; db=sqlite3.connect(sys.argv[1]); result=db.execute("PRAGMA integrity_check").fetchone()[0]; db.close(); raise SystemExit(0 if result == "ok" else 1)'
    [void](Invoke-Checked $python @('-c',$integrityCode,$db) (Join-Path $script:RepoRoot 'backend'))
    Write-Step "Database ready at $db" 'OK';Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
