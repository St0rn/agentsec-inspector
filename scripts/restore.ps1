[CmdletBinding(SupportsShouldProcess,ConfirmImpact='High')]
param([Parameter(Mandatory)][string]$BackupPath,[switch]$Confirmed)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'updates' -ScriptName $MyInvocation.MyCommand.Name
try {
    if(-not(Test-Path $BackupPath)){throw 'Backup archive not found.'};if(-not $Confirmed){throw 'Restoration requires -Confirmed and PowerShell confirmation.'}
    $data=Get-AgentSecDataDir;$stage=Join-Path $env:TEMP ("agentsec-restore-"+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory $stage|Out-Null
    try{Expand-Archive -Path $BackupPath -DestinationPath $stage;if(-not(Test-Path (Join-Path $stage 'agentsec.db')) -or -not(Test-Path (Join-Path $stage 'manifest.json'))){throw 'Invalid backup structure.'};$manifest=Get-Content -Raw (Join-Path $stage 'manifest.json')|ConvertFrom-Json;$dbFile=Join-Path $stage 'agentsec.db';$hash=(Get-FileHash $dbFile -Algorithm SHA256).Hash;if($hash -ne $manifest.database_sha256){throw 'Backup database hash mismatch.'};$header=[Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($dbFile),0,15);if($header -ne 'SQLite format 3'){throw 'Backup does not contain a valid SQLite header.'};& (Join-Path $PSScriptRoot 'backup.ps1');if($LASTEXITCODE){throw 'Safety backup failed.'};Stop-AgentSecProcesses;if($PSCmdlet.ShouldProcess($data,'Replace AgentSec user database and report/evidence directories')){New-Item -ItemType Directory -Force $data|Out-Null;Copy-Item -Force $dbFile (Join-Path $data 'agentsec.db');if(Test-Path (Join-Path $stage '.secret-key')){Copy-Item -Force (Join-Path $stage '.secret-key') $data};foreach($name in @('reports','evidence')){if(Test-Path (Join-Path $stage $name)){Copy-Item -Recurse -Force (Join-Path $stage $name) $data}}}}finally{if(Test-Path $stage){Remove-Item -Recurse -Force $stage}}
    Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';Complete-AgentSecLog 1;exit 1}
