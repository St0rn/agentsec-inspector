[CmdletBinding()]
param([Parameter(Mandatory)][string]$InstallerPath,[Parameter(Mandatory)][version]$TargetVersion)
. (Join-Path $PSScriptRoot 'lib\Common.ps1')
$log=Initialize-AgentSecLog -Category 'updates' -ScriptName $MyInvocation.MyCommand.Name
$backupPath=$null
try {
    if($TargetVersion -le [version]$script:AgentSecVersion){throw "Target version $TargetVersion is not newer than $script:AgentSecVersion."};if(-not(Test-Path $InstallerPath)){throw 'Update installer not found.'}
    & (Join-Path $PSScriptRoot 'backup.ps1');if($LASTEXITCODE){throw 'Pre-update backup failed; update aborted.'};$backupPath=Get-ChildItem -File (Join-Path (Get-AgentSecDataDir) 'backups') -Filter 'agentsec-backup-*.zip'|Sort-Object LastWriteTime -Descending|Select-Object -First 1 -ExpandProperty FullName
    $answer=Read-Host "Install AgentSec $TargetVersion from verified SHA256 $((Get-FileHash $InstallerPath -Algorithm SHA256).Hash)? [y/N]";if($answer -notmatch '^(y|yes|o|oui)$'){throw 'Update cancelled.'}
    if([IO.Path]::GetExtension($InstallerPath)-eq '.msi'){Invoke-Checked msiexec @('/i',$InstallerPath)}else{Invoke-Checked $InstallerPath @()}
    & (Join-Path $PSScriptRoot 'verify-installation.ps1');if($LASTEXITCODE){throw 'Update verification failed. Restore the backup with restore.ps1.'}
    Complete-AgentSecLog 0;exit 0
}catch{Write-Step $_.Exception.Message 'ERROR';if($backupPath -and(Test-Path $backupPath)){Write-Step 'Attempting automatic data rollback from the pre-update backup.' 'WARN';& (Join-Path $PSScriptRoot 'restore.ps1') -BackupPath $backupPath -Confirmed -Confirm:$false;if($LASTEXITCODE){Write-Step 'Automatic rollback failed; preserve the backup and run restore.ps1 manually.' 'ERROR'}else{Write-Step 'Data rollback completed.' 'OK'}};Complete-AgentSecLog 1;exit 1}
